from pathlib import Path

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.core.config import settings
from app.core.llm import get_llm
from app.core.state import AgentState, Finding

_prompt_text = (Path(__file__).parent.parent.parent / "core" / "prompts" / "tests.md").read_text()

prompt = ChatPromptTemplate.from_messages([
    ("system", _prompt_text),
    ("human", "PR Diff:\n{diff}"),
])

tests_chain = prompt | get_llm(json_mode=True) | JsonOutputParser()


def tests_node(state: AgentState) -> dict:
    result = tests_chain.invoke({"diff": state["diff"][: settings.max_diff_tokens]})

    findings: list[Finding] = [
        Finding(agent="tests", **f)
        for f in result.get("findings", [])
    ]

    return {
        "findings": findings,
        "agents_done": state.get("agents_done", []) + ["tests"],
    }
