from collections.abc import Callable
from pathlib import Path

import pytest
from demo_api.chat.graph import build_graph
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.state import CompiledStateGraph


class FakeToolCallingModel(GenericFakeChatModel):
    """A GenericFakeChatModel that tolerates bind_tools - the stock class raises
    NotImplementedError, since BaseChatModel's default implementation is abstract."""

    def bind_tools(self, tools, **kwargs):
        return self


@pytest.fixture
def fake_graph() -> Callable[..., CompiledStateGraph]:
    def build(*replies: AIMessage | str, root: Path | None = None, priming: str | None = None) -> CompiledStateGraph:
        model = FakeToolCallingModel(messages=iter(replies))
        return build_graph(InMemorySaver(), model=model, priming=priming, root=root)

    return build
