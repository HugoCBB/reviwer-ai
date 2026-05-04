from pathlib import Path

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.core.config import settings
from app.core.llm import get_llm
from app.core.state import AgentState

_prompt_text = (Path(__file__).parent.parent.parent / "core" / "prompts" / "orchestrator.md").read_text()

prompt = ChatPromptTemplate.from_messages([
    ("system", _prompt_text),
    ("human", "Title: {title}\nDescription: {description}\nAgents done: {agents_done}\nDiff (excerpt):\n{diff}"),
])

orchestrator_chain = prompt | get_llm(json_mode=True) | JsonOutputParser()

AGENTS = ["security", "quality", "tests", "docs"]


def orchestrator_node(state: AgentState) -> dict:
    result = orchestrator_chain.invoke({
        "agents": AGENTS,
        "agents_done": state.get("agents_done", []),
        "title": state["title"],
        "description": state["description"],
        "diff": state["diff"][: settings.max_diff_tokens],
    })
    return {"next": result["next"]}
