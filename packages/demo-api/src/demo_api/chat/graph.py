from pathlib import Path

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from demo_api.chat.config import REPO_ROOT
from demo_api.chat.model import get_model
from demo_api.chat.priming import render_context_priming
from demo_api.chat.tools import build_tools

SYSTEM_PROMPT = (
    "You are the Crypts and Commits project assistant: a friendly, knowledgeable guide who helps "
    "developers understand this project and answers questions about its current sourcebook - world "
    "context, lore, regions, and campaigns. You have tools to look up live campaign and encounter "
    "status directly from the sourcebook - prefer them over guessing when asked about current status."
)


def _build_prompt(priming: str) -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("system", priming),
            MessagesPlaceholder("messages"),
        ]
    )


def _chat_node(model: BaseChatModel, priming: str, tools: list[BaseTool]):
    chain = _build_prompt(priming) | model.bind_tools(tools)

    def node(state: MessagesState) -> dict:
        response = chain.invoke({"messages": state["messages"]})
        return {"messages": [response]}

    return node


def build_graph(
    checkpointer: BaseCheckpointSaver,
    model: BaseChatModel | None = None,
    priming: str | None = None,
    root: Path | None = None,
) -> CompiledStateGraph:
    resolved_root = root if root is not None else REPO_ROOT
    resolved_priming = priming if priming is not None else render_context_priming(resolved_root)
    tools = build_tools(resolved_root)
    graph = StateGraph(MessagesState)
    graph.add_node("chat", _chat_node(model or get_model(), resolved_priming, tools))
    graph.add_node("tools", ToolNode(tools))
    graph.add_edge(START, "chat")
    graph.add_conditional_edges("chat", tools_condition)
    graph.add_edge("tools", "chat")
    return graph.compile(checkpointer=checkpointer)
