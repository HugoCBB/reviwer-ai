"""
Pytest configuration and shared fixtures for the reviewer-ai test suite.

Environment variables must be set BEFORE any app module is imported because
`app.core.config.Settings` is instantiated at module level by pydantic-settings.
All values here are clearly fake placeholders — no real credentials are needed
because every test mocks external calls (LLM, GitHub API, Celery, Redis).
"""
import os

# Override settings before any app module is imported.
os.environ.setdefault("GOOGLE_API_KEY", "fake-google-key-for-tests")
os.environ.setdefault("GITHUB_TOKEN", "fake-github-token-for-tests")
os.environ.setdefault("GITHUB_SECRET", "test-webhook-secret")
os.environ.setdefault("LLM_PROVIDER", "gemini")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("DEEPSEEK_API_KEY", "fake-deepseek-key-for-tests")

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
