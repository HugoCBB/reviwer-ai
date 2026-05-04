from pathlib import Path

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.core.config import settings
from app.core.llm import get_llm
from app.core.state import AgentState, Finding

_prompt_text = (Path(__file__).parent.parent.parent / "core" / "prompts" / "security.md").read_text()

prompt = ChatPromptTemplate.from_messages([
    ("system", _prompt_text),
    ("human", "PR Diff:\n{diff}"),
])

security_chain = prompt | get_llm(json_mode=True) | JsonOutputParser()


def _normalize(f: dict, agent: str) -> Finding:
    return Finding(
        agent=agent,
        severity=f.get("severity") or "low",
        file=f.get("file") or f.get("path") or "unknown",
        line=int(f.get("line") or f.get("line_number") or 1),
        comment=f.get("comment") or f.get("description") or f.get("message") or "",
    )


def security_node(state: AgentState) -> dict:
    result = security_chain.invoke({"diff": state["diff"][: settings.max_diff_tokens]})

    findings: list[Finding] = [
        _normalize(f, "security")
        for f in result.get("findings", [])
    ]

    return {
        "findings": findings,
        "agents_done": state.get("agents_done", []) + ["security"],
    }
