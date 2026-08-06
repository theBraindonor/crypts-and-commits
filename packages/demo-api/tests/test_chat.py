import json
import uuid

import pytest
from demo_api.chat.graph import build_graph
from demo_api.main import app, get_graph
from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.state import CompiledStateGraph


def _fake_graph(*replies: str) -> CompiledStateGraph:
    model = GenericFakeChatModel(messages=iter(replies))
    return build_graph(InMemorySaver(), model=model)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def _clear_overrides():
    yield
    app.dependency_overrides.pop(get_graph, None)


def _parse_stream(text: str) -> list[dict]:
    return [json.loads(line) for line in text.splitlines() if line]


def test_chat_streams_multiple_chunks(client: TestClient) -> None:
    app.dependency_overrides[get_graph] = lambda: _fake_graph("Hello there, friend!")

    response = client.post("/chat", json={"message": "hi"})

    assert response.status_code == 200
    chunks = _parse_stream(response.text)
    assert len(chunks) > 1
    assert "".join(chunk["content"] for chunk in chunks) == "Hello there, friend!"


def test_chat_generates_thread_id_when_omitted(client: TestClient) -> None:
    app.dependency_overrides[get_graph] = lambda: _fake_graph("Hi!")

    response = client.post("/chat", json={"message": "hi"})

    thread_id = response.headers["X-Thread-Id"]
    assert uuid.UUID(thread_id).version == 7


def test_chat_reused_thread_id_continues_conversation(client: TestClient) -> None:
    graph = _fake_graph("First reply.", "Second reply.")
    app.dependency_overrides[get_graph] = lambda: graph

    first = client.post("/chat", json={"message": "hi"})
    thread_id = first.headers["X-Thread-Id"]

    client.post("/chat", json={"thread_id": thread_id, "message": "again"})

    state = graph.get_state({"configurable": {"thread_id": thread_id}})
    assert len(state.values["messages"]) == 4


def test_chat_new_thread_id_starts_fresh(client: TestClient) -> None:
    graph = _fake_graph("Reply one.", "Reply two.")
    app.dependency_overrides[get_graph] = lambda: graph

    first = client.post("/chat", json={"message": "hi"})
    second = client.post("/chat", json={"message": "hi again"})

    thread_a = first.headers["X-Thread-Id"]
    thread_b = second.headers["X-Thread-Id"]
    assert thread_a != thread_b

    state_a = graph.get_state({"configurable": {"thread_id": thread_a}})
    assert len(state_a.values["messages"]) == 2
