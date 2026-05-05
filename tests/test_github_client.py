import json

import httpx
import pytest
import respx

from app.api.github_client import GITHUB_API, get_pr_diff, post_review
from app.core.state import Finding

_REPO = "org/repo"
_PR = 42


class TestGetPrDiff:
    def test_returns_diff_text(self):
        with respx.mock:
            respx.get(f"{GITHUB_API}/repos/{_REPO}/pulls/{_PR}").mock(
                return_value=httpx.Response(200, text="--- a/file.py\n+++ b/file.py")
            )
            result = get_pr_diff(_REPO, _PR)
        assert result == "--- a/file.py\n+++ b/file.py"

    def test_raises_on_http_error(self):
        with respx.mock:
            respx.get(f"{GITHUB_API}/repos/{_REPO}/pulls/{_PR}").mock(
                return_value=httpx.Response(404)
            )
            with pytest.raises(httpx.HTTPStatusError):
                get_pr_diff(_REPO, _PR)

    def test_uses_diff_accept_header(self):
        with respx.mock:
            route = respx.get(f"{GITHUB_API}/repos/{_REPO}/pulls/{_PR}").mock(
                return_value=httpx.Response(200, text="diff")
            )
            get_pr_diff(_REPO, _PR)
        assert route.called
        sent_accept = route.calls.last.request.headers["accept"]
        assert "diff" in sent_accept


class TestPostReview:
    def _make_finding(self, severity: str = "high") -> Finding:
        return Finding(
            agent="security",
            severity=severity,
            file="app/main.py",
            line=10,
            comment="Issue found",
        )

    def test_request_changes_when_critical_finding(self):
        with respx.mock:
            route = respx.post(f"{GITHUB_API}/repos/{_REPO}/pulls/{_PR}/reviews").mock(
                return_value=httpx.Response(200, json={"id": 1})
            )
            post_review(_REPO, _PR, [self._make_finding("critical")], "Summary")
        body = json.loads(route.calls.last.request.content)
        assert body["event"] == "REQUEST_CHANGES"

    def test_comment_when_no_critical_findings(self):
        with respx.mock:
            route = respx.post(f"{GITHUB_API}/repos/{_REPO}/pulls/{_PR}/reviews").mock(
                return_value=httpx.Response(200, json={"id": 1})
            )
            post_review(_REPO, _PR, [self._make_finding("high")], "Summary")
        body = json.loads(route.calls.last.request.content)
        assert body["event"] == "COMMENT"

    def test_summary_only_when_no_file_findings(self):
        with respx.mock:
            respx.post(f"{GITHUB_API}/repos/{_REPO}/pulls/{_PR}/reviews").mock(
                return_value=httpx.Response(200, json={"id": 1})
            )
            post_review(_REPO, _PR, [], "Just a summary")

    def test_body_includes_details_when_findings_have_file(self):
        with respx.mock:
            route = respx.post(f"{GITHUB_API}/repos/{_REPO}/pulls/{_PR}/reviews").mock(
                return_value=httpx.Response(200, json={"id": 1})
            )
            post_review(_REPO, _PR, [self._make_finding()], "Summary text")
        body = json.loads(route.calls.last.request.content)
        assert "Summary text" in body["body"]
        assert "Detalhes por agente" in body["body"]

    def test_raises_on_http_error(self):
        with respx.mock:
            respx.post(f"{GITHUB_API}/repos/{_REPO}/pulls/{_PR}/reviews").mock(
                return_value=httpx.Response(422, json={"message": "Unprocessable"})
            )
            with pytest.raises(httpx.HTTPStatusError):
                post_review(_REPO, _PR, [], "Summary")
