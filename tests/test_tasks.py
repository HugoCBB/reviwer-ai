from unittest.mock import patch

import pytest
from celery.exceptions import SoftTimeLimitExceeded

from app.api.tasks import review_pr

_PR_DATA = {
    "repo": "org/repo",
    "number": 42,
    "title": "feat: new feature",
    "body": "PR description",
}

_GRAPH_RESULT = {
    "findings": [],
    "summary": "No issues found.",
}


class TestReviewPrTask:
    def test_happy_path_calls_all_steps(self):
        with (
            patch("app.api.tasks.get_pr_diff", return_value="diff content") as mock_diff,
            patch("app.api.tasks.pr_reviewer_graph") as mock_graph,
            patch("app.api.tasks.post_review") as mock_post,
        ):
            mock_graph.invoke.return_value = _GRAPH_RESULT
            review_pr.run(_PR_DATA)

        mock_diff.assert_called_once_with("org/repo", 42)
        mock_graph.invoke.assert_called_once()
        mock_post.assert_called_once_with(
            repo="org/repo",
            pr_number=42,
            findings=[],
            summary="No issues found.",
        )

    def test_graph_receives_correct_initial_state(self):
        with (
            patch("app.api.tasks.get_pr_diff", return_value="the diff"),
            patch("app.api.tasks.pr_reviewer_graph") as mock_graph,
            patch("app.api.tasks.post_review"),
        ):
            mock_graph.invoke.return_value = _GRAPH_RESULT
            review_pr.run(_PR_DATA)

        state = mock_graph.invoke.call_args[0][0]
        assert state["pr_number"] == 42
        assert state["repo"] == "org/repo"
        assert state["diff"] == "the diff"
        assert state["title"] == "feat: new feature"
        assert state["description"] == "PR description"
        assert state["findings"] == []
        assert state["agents_done"] == []

    def test_none_body_becomes_empty_description(self):
        pr_data = {**_PR_DATA, "body": None}
        with (
            patch("app.api.tasks.get_pr_diff", return_value="diff"),
            patch("app.api.tasks.pr_reviewer_graph") as mock_graph,
            patch("app.api.tasks.post_review"),
        ):
            mock_graph.invoke.return_value = _GRAPH_RESULT
            review_pr.run(pr_data)

        state = mock_graph.invoke.call_args[0][0]
        assert state["description"] == ""

    def test_soft_timeout_posts_warning_review(self):
        with (
            patch("app.api.tasks.get_pr_diff", side_effect=SoftTimeLimitExceeded()),
            patch("app.api.tasks.post_review") as mock_post,
        ):
            review_pr.run(_PR_DATA)

        mock_post.assert_called_once()
        kwargs = mock_post.call_args[1]
        assert kwargs["repo"] == "org/repo"
        assert kwargs["pr_number"] == 42
        assert kwargs["findings"] == []
        assert "timed out" in kwargs["summary"].lower() or "timeout" in kwargs["summary"].lower()

    def test_exception_triggers_retry(self):
        with (
            patch("app.api.tasks.get_pr_diff", side_effect=ConnectionError("Network down")),
            patch.object(review_pr, "retry", side_effect=ConnectionError("retry raised")) as mock_retry,
        ):
            with pytest.raises(ConnectionError, match="retry raised"):
                review_pr.run(_PR_DATA)

        mock_retry.assert_called_once()
        retry_kwargs = mock_retry.call_args[1]
        assert isinstance(retry_kwargs["exc"], ConnectionError)
        assert retry_kwargs["countdown"] > 0
