"""
Pytest configuration and shared fixtures for the reviewer-ai test suite.

Environment variables must be set BEFORE any app module is imported because:
1. `app.core.config.Settings` is instantiated at module level by pydantic-settings.
2. Agent modules create LLM chains at module level; ChatGoogleGenerativeAI validates
   that GOOGLE_API_KEY is non-empty at instantiation time (not at call time).

We use `os.environ.get() or "fallback"` instead of `setdefault` because GitHub Actions
evaluates `${{ secrets.NAME }}` to an empty string when the secret is not configured,
and `setdefault` does not override an existing empty string.

All values here are fake placeholders — no real credentials are used because every
test mocks external calls (LLM, GitHub API, Celery, Redis) via respx/pytest-mock.
"""
import os

# Force non-empty values — handles both "key absent" and "key set to empty string".
os.environ["GOOGLE_API_KEY"] = os.environ.get("GOOGLE_API_KEY") or "fake-google-key-for-tests"
os.environ["GITHUB_TOKEN"] = os.environ.get("GITHUB_TOKEN") or "fake-github-token-for-tests"
os.environ["GITHUB_SECRET"] = os.environ.get("GITHUB_SECRET") or "test-webhook-secret"
os.environ["DEEPSEEK_API_KEY"] = os.environ.get("DEEPSEEK_API_KEY") or "fake-deepseek-key-for-tests"
os.environ.setdefault("LLM_PROVIDER", "gemini")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

import pytest

from app.core.state import AgentState, Finding


@pytest.fixture()
def base_state() -> AgentState:
    """Minimal valid AgentState for use in agent node tests."""
    return AgentState(
        pr_number=1,
        repo="org/repo",
        diff="--- a/file.py\n+++ b/file.py\n@@ -1 +1 @@\n-old\n+new",
        title="feat: example PR",
        description="A sample PR for testing",
        findings=[],
        agents_done=[],
        next="",
        summary="",
        previous_findings=[],
        previous_summary="",
    )


@pytest.fixture()
def sample_finding() -> Finding:
    """A single Finding with all fields populated."""
    return Finding(
        agent="security",
        severity="high",
        file="app/main.py",
        line=42,
        comment="Potential SQL injection",
    )


@pytest.fixture()
def multi_findings() -> list[Finding]:
    """A mixed-severity list of findings for aggregation tests."""
    return [
        Finding(agent="security", severity="critical", file="app/auth.py", line=10, comment="Hardcoded secret"),
        Finding(agent="quality", severity="medium", file="app/utils.py", line=5, comment="Long function"),
        Finding(agent="docs", severity="low", file="app/api.py", line=1, comment="Missing docstring"),
    ]
