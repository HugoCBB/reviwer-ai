import hashlib
import hmac
import json
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.api.main import _verify_signature, app
from app.core.config import settings

client = TestClient(app)

_SECRET = settings.github_webhook_secret


def _sign(payload: bytes, secret: str = _SECRET) -> str:
    digest = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def _post_webhook(payload: dict, event: str = "pull_request", secret: str = _SECRET):
    body = json.dumps(payload).encode()
    return client.post(
        "/webhook/github",
        content=body,
        headers={
            "X-GitHub-Event": event,
            "X-Hub-Signature-256": _sign(body, secret),
            "Content-Type": "application/json",
        },
    )


_PR_PAYLOAD = {
    "action": "opened",
    "pull_request": {
        "number": 42,
        "title": "feat: new feature",
        "body": "PR description",
    },
    "repository": {"full_name": "org/repo"},
}


class TestVerifySignature:
    def test_valid_signature(self):
        payload = b'{"key": "value"}'
        assert _verify_signature(payload, _sign(payload)) is True

    def test_invalid_signature(self):
        assert _verify_signature(b"data", "sha256=badhex") is False

    def test_tampered_payload(self):
        payload = b'{"key": "value"}'
        sig = _sign(payload)
        assert _verify_signature(b"tampered", sig) is False

    def test_wrong_secret(self):
        payload = b"data"
        sig = _sign(payload, secret="wrong-secret")
        assert _verify_signature(payload, sig) is False


class TestHealthEndpoint:
    def test_returns_ok(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestGithubWebhook:
    def test_invalid_signature_returns_401(self):
        body = json.dumps(_PR_PAYLOAD).encode()
        response = client.post(
            "/webhook/github",
            content=body,
            headers={
                "X-GitHub-Event": "pull_request",
                "X-Hub-Signature-256": "sha256=invalidsig",
                "Content-Type": "application/json",
            },
        )
        assert response.status_code == 401

    @patch("app.api.main.review_pr")
    def test_pr_opened_enqueues_task(self, mock_review_pr):
        payload = {**_PR_PAYLOAD, "action": "opened"}
        response = _post_webhook(payload)
        assert response.status_code == 200
        assert response.json() == {"status": "accepted"}
        mock_review_pr.delay.assert_called_once()

    @patch("app.api.main.review_pr")
    def test_pr_synchronize_enqueues_task(self, mock_review_pr):
        payload = {**_PR_PAYLOAD, "action": "synchronize"}
        _post_webhook(payload)
        mock_review_pr.delay.assert_called_once()

    @patch("app.api.main.review_pr")
    def test_pr_closed_does_not_enqueue(self, mock_review_pr):
        payload = {**_PR_PAYLOAD, "action": "closed"}
        response = _post_webhook(payload)
        assert response.status_code == 200
        mock_review_pr.delay.assert_not_called()

    @patch("app.api.main.review_pr")
    def test_non_pr_event_returns_accepted_without_task(self, mock_review_pr):
        response = _post_webhook({"zen": "Simple things.", "hook_id": 1}, event="ping")
        assert response.status_code == 200
        mock_review_pr.delay.assert_not_called()

    @patch("app.api.main.review_pr")
    def test_task_receives_correct_pr_data(self, mock_review_pr):
        _post_webhook(_PR_PAYLOAD)
        call_arg = mock_review_pr.delay.call_args[0][0]
        assert call_arg["number"] == 42
        assert call_arg["repo"] == "org/repo"
        assert call_arg["title"] == "feat: new feature"
        assert call_arg["body"] == "PR description"

    @patch("app.api.main.review_pr")
    def test_pr_with_null_body(self, mock_review_pr):
        payload = {
            **_PR_PAYLOAD,
            "pull_request": {**_PR_PAYLOAD["pull_request"], "body": None},
        }
        _post_webhook(payload)
        call_arg = mock_review_pr.delay.call_args[0][0]
        assert call_arg["body"] is None
