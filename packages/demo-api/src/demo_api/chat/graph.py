from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph

from demo_api.chat.config import REPO_ROOT
from demo_api.chat.model import get_model
from demo_api.chat.priming import render_context_priming

SYSTEM_PROMPT = (
    "You are the Crypts and Commits project assistant: a friendly, knowledgeable guide who helps "
    "developers understand this project and answers questions about its current sourcebook - world "
    "context, lore, regions, and campaigns."
)


def _build_prompt(priming: str) -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("system", priming),
            MessagesPlaceholder("messages"),
        ]
    )


def _chat_node(model: BaseChatModel, priming: str):
    chain = _build_prompt(priming) | model

    def node(state: MessagesState) -> dict:
        response = chain.invoke({"messages": state["messages"]})
        return {"messages": [response]}

    return node


def build_graph(
    checkpointer: BaseCheckpointSaver,
    model: BaseChatModel | None = None,
    priming: str | None = None,
) -> CompiledStateGraph:
    resolved_priming = priming if priming is not None else render_context_priming(REPO_ROOT)
    graph = StateGraph(MessagesState)
    graph.add_node("chat", _chat_node(model or get_model(), resolved_priming))
    graph.add_edge(START, "chat")
    graph.add_edge("chat", END)
    return graph.compile(checkpointer=checkpointer)
