from unittest.mock import patch

from app.core.state import Finding
from app.modules.agents.aggregator_agent import aggregator_node

_BASE_STATE = {
    "pr_number": 1,
    "repo": "org/repo",
    "diff": "some diff",
    "title": "Test PR",
    "description": "",
    "agents_done": [],
    "next": "",
    "summary": "",
}


class TestAggregatorNode:
    def test_returns_summary_and_finish(self):
        state = {**_BASE_STATE, "findings": [
            Finding(agent="security", severity="high", file="app/main.py", line=10, comment="SQL injection"),
        ]}
        with patch("app.modules.agents.aggregator_agent.aggregator_chain") as mock_chain:
            mock_chain.invoke.return_value = "Security issues found."
            result = aggregator_node(state)

        assert result["next"] == "FINISH"
        assert result["summary"] == "Security issues found."

    def test_empty_findings_sends_no_issues_message(self):
        state = {**_BASE_STATE, "findings": []}
        with patch("app.modules.agents.aggregator_agent.aggregator_chain") as mock_chain:
            mock_chain.invoke.return_value = "No issues."
            aggregator_node(state)

        call_kwargs = mock_chain.invoke.call_args[0][0]
        assert call_kwargs["findings"] == "No issues found by any agent."

    def test_findings_are_formatted_correctly(self):
        state = {**_BASE_STATE, "findings": [
            Finding(agent="security", severity="critical", file="app/auth.py", line=42, comment="Hardcoded secret"),
            Finding(agent="quality", severity="low", file="app/utils.py", line=5, comment="Long function"),
        ]}
        with patch("app.modules.agents.aggregator_agent.aggregator_chain") as mock_chain:
            mock_chain.invoke.return_value = "Summary"
            aggregator_node(state)

        formatted = mock_chain.invoke.call_args[0][0]["findings"]
        assert "[SECURITY]" in formatted
        assert "[CRITICAL]" in formatted
        assert "app/auth.py:42" in formatted
        assert "Hardcoded secret" in formatted
        assert "[QUALITY]" in formatted
        assert "[LOW]" in formatted
        assert "app/utils.py:5" in formatted

    def test_agent_and_severity_are_uppercased(self):
        state = {**_BASE_STATE, "findings": [
            Finding(agent="docs", severity="medium", file="app/api.py", line=1, comment="Missing docstring"),
        ]}
        with patch("app.modules.agents.aggregator_agent.aggregator_chain") as mock_chain:
            mock_chain.invoke.return_value = ""
            aggregator_node(state)

        formatted = mock_chain.invoke.call_args[0][0]["findings"]
        assert "[DOCS]" in formatted
        assert "[MEDIUM]" in formatted

    def test_multiple_findings_are_newline_separated(self):
        state = {**_BASE_STATE, "findings": [
            Finding(agent="security", severity="high", file="a.py", line=1, comment="A"),
            Finding(agent="quality", severity="low", file="b.py", line=2, comment="B"),
        ]}
        with patch("app.modules.agents.aggregator_agent.aggregator_chain") as mock_chain:
            mock_chain.invoke.return_value = ""
            aggregator_node(state)

        formatted = mock_chain.invoke.call_args[0][0]["findings"]
        lines = formatted.strip().splitlines()
        assert len(lines) == 2
