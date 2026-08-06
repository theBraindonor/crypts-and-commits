from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph

from demo_api.chat.model import get_model

SYSTEM_PROMPT = "You are a friendly assistant."

_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder("messages"),
    ]
)


def _chat_node(model: BaseChatModel):
    chain = _prompt | model

    def node(state: MessagesState) -> dict:
        response = chain.invoke({"messages": state["messages"]})
        return {"messages": [response]}

    return node


def build_graph(checkpointer: BaseCheckpointSaver, model: BaseChatModel | None = None) -> CompiledStateGraph:
    graph = StateGraph(MessagesState)
    graph.add_node("chat", _chat_node(model or get_model()))
    graph.add_edge(START, "chat")
    graph.add_edge("chat", END)
    return graph.compile(checkpointer=checkpointer)
