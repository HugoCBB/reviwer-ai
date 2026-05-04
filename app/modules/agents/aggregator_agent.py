from pathlib import Path

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.core.llm import get_llm
from app.core.state import AgentState

_prompt_text = (Path(__file__).parent.parent.parent / "core" / "prompts" / "aggregator.md").read_text()

prompt = ChatPromptTemplate.from_messages([
    ("system", _prompt_text),
    ("human", "Findings from all agents:\n{findings}"),
])

aggregator_chain = prompt | get_llm() | StrOutputParser()


def aggregator_node(state: AgentState) -> dict:
    findings = state.get("findings", [])

    formatted = "\n".join(
        f"[{f['agent'].upper()}] [{f['severity'].upper()}] {f['file']}:{f['line']} — {f['comment']}"
        for f in findings
    ) or "No issues found by any agent."

    summary = aggregator_chain.invoke({"findings": formatted})

    return {"summary": summary, "next": "FINISH"}
