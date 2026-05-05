from unittest.mock import patch

from app.modules.agents.security_agent import _normalize, security_node

_BASE_STATE = {
    "pr_number": 1,
    "repo": "org/repo",
    "diff": "some diff content",
    "title": "Test PR",
    "description": "",
    "findings": [],
    "agents_done": [],
    "next": "",
    "summary": "",
}


class TestNormalize:
    def test_full_finding(self):
        raw = {"severity": "high", "file": "app/main.py", "line": 10, "comment": "Issue"}
        result = _normalize(raw, "security")
        assert result == {
            "agent": "security",
            "severity": "high",
            "file": "app/main.py",
            "line": 10,
            "comment": "Issue",
        }

    def test_missing_severity_defaults_to_low(self):
        raw = {"file": "app/main.py", "line": 1, "comment": "Minor"}
        assert _normalize(raw, "security")["severity"] == "low"

    def test_file_falls_back_to_path_key(self):
        raw = {"severity": "medium", "path": "app/routes.py", "line": 5, "comment": "Issue"}
        assert _normalize(raw, "security")["file"] == "app/routes.py"

    def test_missing_file_and_path_defaults_to_unknown(self):
        raw = {"severity": "low", "line": 1, "comment": "Issue"}
        assert _normalize(raw, "security")["file"] == "unknown"

    def test_missing_line_defaults_to_1(self):
        raw = {"severity": "low", "file": "app/main.py", "comment": "Issue"}
        assert _normalize(raw, "security")["line"] == 1

    def test_line_number_field_used_as_fallback(self):
        raw = {"severity": "low", "file": "app/main.py", "line_number": 99, "comment": "Issue"}
        assert _normalize(raw, "security")["line"] == 99

    def test_comment_falls_back_to_description(self):
        raw = {"severity": "low", "file": "app/main.py", "line": 1, "description": "Desc text"}
        assert _normalize(raw, "security")["comment"] == "Desc text"

    def test_comment_falls_back_to_message(self):
        raw = {"severity": "low", "file": "app/main.py", "line": 1, "message": "Msg text"}
        assert _normalize(raw, "security")["comment"] == "Msg text"

    def test_agent_name_is_preserved(self):
        raw = {"severity": "low", "file": "f.py", "line": 1, "comment": "X"}
        assert _normalize(raw, "quality")["agent"] == "quality"

    def test_line_is_cast_to_int(self):
        raw = {"severity": "low", "file": "f.py", "line": "42", "comment": "X"}
        result = _normalize(raw, "security")
        assert result["line"] == 42
        assert isinstance(result["line"], int)


class TestSecurityNode:
    def test_returns_normalized_findings(self):
        state = {**_BASE_STATE, "diff": "vulnerable code"}
        mock_result = {
            "findings": [
                {"severity": "high", "file": "app/main.py", "line": 10, "comment": "SQL injection"},
            ]
        }
        with patch("app.modules.agents.security_agent.security_chain") as mock_chain:
            mock_chain.invoke.return_value = mock_result
            result = security_node(state)

        assert len(result["findings"]) == 1
        assert result["findings"][0]["agent"] == "security"
        assert result["findings"][0]["severity"] == "high"

    def test_appends_security_to_agents_done(self):
        state = {**_BASE_STATE, "agents_done": ["quality"]}
        with patch("app.modules.agents.security_agent.security_chain") as mock_chain:
            mock_chain.invoke.return_value = {"findings": []}
            result = security_node(state)

        assert result["agents_done"] == ["quality", "security"]

    def test_empty_findings_returns_empty_list(self):
        with patch("app.modules.agents.security_agent.security_chain") as mock_chain:
            mock_chain.invoke.return_value = {"findings": []}
            result = security_node({**_BASE_STATE})

        assert result["findings"] == []

    def test_diff_is_truncated_to_max_tokens(self):
        long_diff = "x" * 10_000
        state = {**_BASE_STATE, "diff": long_diff}
        with patch("app.modules.agents.security_agent.security_chain") as mock_chain:
            mock_chain.invoke.return_value = {"findings": []}
            security_node(state)

        sent_diff = mock_chain.invoke.call_args[0][0]["diff"]
        assert len(sent_diff) <= 4_000

    def test_missing_findings_key_returns_empty(self):
        with patch("app.modules.agents.security_agent.security_chain") as mock_chain:
            mock_chain.invoke.return_value = {}
            result = security_node({**_BASE_STATE})

        assert result["findings"] == []
