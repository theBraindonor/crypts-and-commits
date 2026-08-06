import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import uuid6
from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel

from demo_api.chat.graph import build_graph

DATA_DIR = Path(__file__).resolve().parent.parent.parent / ".data"
CHECKPOINT_DB_PATH = DATA_DIR / "chat.sqlite"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    async with AsyncSqliteSaver.from_conn_string(str(CHECKPOINT_DB_PATH)) as checkpointer:
        app.state.graph = build_graph(checkpointer)
        yield


app = FastAPI(
    title="Crypts and Commits Demo API",
    description="A Coding Assistant Continuity Framework. Demonstration API",
    lifespan=lifespan,
)

INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Crypts and Commits Demo API</title>
</head>
<body>
    <h1>Crypts and Commits Demo API</h1>
    <p><a href="/docs">API documentation (Swagger UI)</a></p>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return INDEX_HTML


@app.get("/health")
def health() -> dict[str, bool]:
    return {"success": True}


def get_graph(request: Request) -> CompiledStateGraph:
    return request.app.state.graph


class ChatRequest(BaseModel):
    thread_id: str | None = None
    message: str


_graph_dependency = Depends(get_graph)


@app.post("/chat")
async def chat(chat_request: ChatRequest, graph: CompiledStateGraph = _graph_dependency) -> StreamingResponse:
    thread_id = chat_request.thread_id or str(uuid6.uuid7())

    async def token_stream() -> AsyncIterator[str]:
        async for event in graph.astream_events(
            {"messages": [HumanMessage(content=chat_request.message)]},
            config={"configurable": {"thread_id": thread_id}},
            version="v2",
        ):
            if event["event"] == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    yield json.dumps({"content": content}) + "\n"

    return StreamingResponse(
        token_stream(),
        media_type="application/x-ndjson",
        headers={"X-Thread-Id": thread_id},
    )
