---
archived: true
campaign: v0.1.7-rag-demo-application
created_by: John Hoff
created_on: '2026-08-05T21:25:39Z'
depends_on:
- bootstrap-fastapi-app-shell
name: add-streaming-chat-endpoint
regions:
- demo-api
status: completed
updated_by: John Hoff
updated_on: '2026-08-09T14:09:04Z'
---

## Requirements

- `packages/demo-api` exposes `POST /chat`, accepting a JSON body with an **optional** `thread_id` (string) and a required `message` (the human's chat message, string).
- When `thread_id` is omitted, the API generates a new one (a **UUIDv7**) rather than accepting client-supplied ids by default - keeping thread-id creation under the API's control. The generated (or client-supplied) `thread_id` is returned to the caller via an `X-Thread-Id` response header, set before the streamed body begins.
- The endpoint streams the LangGraph agent's response as it is generated (a chunked HTTP response), rather than waiting for the full completion before responding.
- The agent is built with **LangGraph**: a single-node graph is sufficient for this milestone (no tools yet), using a standard chat-prompt structure (system prompt + conversation history + new human turn via `ChatPromptTemplate`) so multi-turn conversations work.
- The system prompt is exactly "You are a friendly assistant."
- Model access goes through **OpenRouter** via `langchain-openai`'s `ChatOpenAI` pointed at OpenRouter's OpenAI-compatible endpoint. The OpenRouter API key and target model id are read from environment variables, loaded via **python-dotenv** from a `.env` file (gitignored; a `.env.example` documents the required keys without real values). The model defaults to `google/gemma-4-31b-it:free` when unset.
- Conversation state is persisted per `thread_id` using **LangGraph's SQLite checkpointer**, so a second request with the same `thread_id` (whether client-supplied or previously server-generated) continues the same conversation, and a different/new `thread_id` starts fresh.
- New dependencies (`langgraph`, its SQLite checkpointer package, `langchain-openai`, `python-dotenv`, `uuid6` for UUIDv7 generation) are declared in `packages/demo-api`'s `pyproject.toml` and locked in the root `pdm.lock`.
- Automated tests cover `/chat` without making real network calls to OpenRouter (the chat model is swappable/fakeable for tests) and pass under `pdm run pytest -q`.
- `pdm run ruff check .` / `ruff format .` stay clean across the new code.
- Explicitly out of scope for this encounter: RAG/`.sourcebook` retrieval, real tool calling, and any `demo-ui`-side wiring of this endpoint - this is backend plumbing only, per the user's framing ("focusing entirely on getting all of the components wired up, and not... the actual agent functionality").

## Rationale

- This is the second concrete step of `demo-api` within `v0.1.7-rag-demo-application`, following `bootstrap-fastapi-app-shell`'s bare HTTP shell. It settles the "concrete LLM/agent orchestration approach" the campaign body and `demo-api` region flagged as unconfirmed - LangGraph + OpenRouter, not the region's original placeholder guess of "a LangChain agent over swappable OpenAI/Anthropic models" - per the user's explicit direction and the region-doc update made alongside this encounter.
- Scope is deliberately narrow, mirroring both prior encounters in this campaign: get the plumbing (streaming, multi-turn state, model access, prompt structure) working end-to-end first, before any real agent behavior (RAG grounding, tools) is layered on. A single-node graph is the smallest thing that can meaningfully prove LangGraph's streaming and checkpointing work through FastAPI.
- SQLite checkpointing is chosen (over in-memory) specifically so multi-turn behavior survives across separate HTTP requests, which is the realistic shape of a browser-based chat client - not just within one process's memory during a single call.
- Server-generated `thread_id`s (UUIDv7, chosen over UUIDv4 for its time-ordered/sortable property) put the API in control of identifier creation and format, rather than trusting arbitrary client-supplied strings as LangGraph checkpoint keys; a client can still resume a specific conversation by supplying a `thread_id` it was previously given. A response header (rather than folding it into the streamed body) keeps the NDJSON stream homogeneous - every line is a token delta - while still making the id available to the caller before or during consumption of the stream.
- Testing without real OpenRouter calls is a hard requirement, not a nice-to-have: `clean-tests-and-lint` (world-assigned lore) requires `pdm run pytest -q` to pass, and a suite that depends on a live API key/network access would be flaky and unsuitable for CI or a fresh contributor's first run.

## Plan

1. Add dependencies: `pdm add -p packages/demo-api langgraph langgraph-checkpoint-sqlite langchain-openai python-dotenv uuid6` (run from the repo root), updating `packages/demo-api/pyproject.toml` and root `pdm.lock`.
2. Add `packages/demo-api/.env.example` documenting `OPENROUTER_API_KEY` and `CHAT_MODEL` (noting the `google/gemma-4-31b-it:free` default). Add `.env` and a local SQLite data directory (e.g. `packages/demo-api/.data/`) to the root `.gitignore` (currently has no `.env`/sqlite-data patterns at all) so secrets and local conversation state are never committed.
3. Create `packages/demo-api/src/demo_api/chat/__init__.py` and:
   - `config.py`: calls `dotenv.load_dotenv()` and reads `OPENROUTER_API_KEY` / `CHAT_MODEL` (default `"google/gemma-4-31b-it:free"`) into simple accessors.
   - `model.py`: a `get_model()` factory building `ChatOpenAI(model=..., api_key=..., base_url="https://openrouter.ai/api/v1", streaming=True)` from `config.py`'s values.
   - `graph.py`: builds a LangGraph `StateGraph` over the prebuilt `MessagesState`, with one node that renders a `ChatPromptTemplate` (system message "You are a friendly assistant." + `MessagesPlaceholder("messages")`) and invokes the model from `model.py`; wires `START -> node -> END`. Exposes `build_graph(checkpointer)` so the checkpointer's open/close lifecycle is managed by the app, not this module.
4. In `packages/demo-api/src/demo_api/main.py`, add a FastAPI `lifespan` context manager that opens `AsyncSqliteSaver` against `packages/demo-api/.data/chat.sqlite` for the app's lifetime, calls `build_graph(checkpointer)`, and stores the compiled graph via a FastAPI dependency (e.g. `get_graph(request: Request)` reading `request.app.state.graph`) so tests can override it with `app.dependency_overrides`.
5. Add `POST /chat` in `main.py`: a Pydantic `ChatRequest {thread_id: str | None = None, message: str}` model. The handler depends on `get_graph`; if `thread_id` is `None`, generates one via `str(uuid6.uuid7())`; calls `graph.astream_events({"messages": [HumanMessage(content=message)]}, config={"configurable": {"thread_id": thread_id}}, version="v2")`, filters for `on_chat_model_stream` events, and streams each token delta as a newline-delimited JSON line (`{"content": "..."}`) via `StreamingResponse`, setting the `X-Thread-Id` response header to the resolved `thread_id` before streaming begins.
6. Add `packages/demo-api/tests/test_chat.py`: override the `get_graph` dependency with a graph built against `langchain_core.language_models.fake_chat_models.GenericFakeChatModel` (no real network calls) and an in-memory/temp-file checkpointer. Assert: `POST /chat` returns 200 and streams multiple chunks whose concatenated content matches the fake model's canned reply; a request with no `thread_id` returns a valid UUID string in the `X-Thread-Id` header; reusing a `thread_id` (client-supplied, or one captured from a prior response's `X-Thread-Id` header) across two requests continues the same checkpointed thread (e.g. the second call's graph state includes the first turn's messages), while a different/omitted `thread_id` does not.
7. Run `pdm install` to resolve the new dependencies into the workspace `.venv`.

## Verification

- `pdm run pytest -q` passes, including the new `demo-api` chat tests, without requiring a real `OPENROUTER_API_KEY` or network access.
- `pdm run ruff check .` reports zero errors; `pdm run ruff format .` reports no diffs.
- Manual local run (developer supplies a real `.env`/`OPENROUTER_API_KEY`): start the server, `POST /chat` with just a `message` (no `thread_id`) via curl/httpie, confirm the response streams incrementally and that the `X-Thread-Id` response header contains a generated UUID; repeat the request supplying that captured `thread_id`, and confirm the reply is consistent with the model having seen the first turn.

## Log

### Review - 2026-08-05T22:41:42Z - John Hoff

Reviewed against the sole applicable lore item, `clean-tests-and-lint` (world-assigned; the `demo-api` region carries no additional assigned lore) — the Plan's Verification section explicitly commits to `pdm run pytest -q` passing without live network/API-key dependence (via a dependency-injected fake chat model) and to clean `ruff check`/`ruff format`, with no skip markers, `--no-verify`, or `# noqa` suppressions anywhere in the Plan, fully honoring the gate. The Plan is also internally consistent with the `demo-api` region's confirmed technology decisions (LangGraph, OpenRouter via `langchain-openai`, `.env`-driven config, SQLite checkpointing, the exact system prompt) and correctly keeps RAG/tool-calling/`demo-ui` wiring out of scope per that region's "still to confirm" list. Two items are noted as unverified rather than blocking: whether `GenericFakeChatModel` and `uuid6.uuid7()` exist as invoked in the dependency versions this Plan would pull in, which is a dependency-resolution question outside this lore-focused review's scope, not a lore conflict.

### Message - 2026-08-06T04:18:17Z - John Hoff

Implementation notes, no Requirements/scope deviation: (1) config.py originally called load_dotenv() with no path, which searches upward from the current working directory rather than from the package - since the manual-run command is launched from the repo root (per the Plan/README's documented `pdm run uvicorn ... --app-dir packages/demo-api/src`), it never found packages/demo-api/.env. Fixed by resolving the .env path explicitly relative to config.py's own file location (DEMO_API_ROOT = 4 parents up), matching the same pattern main.py already uses for its .data directory. (2) Manual verification surfaced two environment issues unrelated to the code: the GM's initial .env key was malformed (missing OpenRouter's "sk-or-v1-" prefix, confirmed independently via a raw HTTP request bypassing langchain entirely) and, after that was corrected, the initially-requested google/gemma-4-31b-it:free model was rate-limited on OpenRouter's shared free-tier pool. The GM switched CHAT_MODEL to the non-free google/gemma-4-31b-it to complete verification; google/gemma-4-31b-it:free remains the code's documented default in .env.example per the Requirements, this was only a local override for testing. With both resolved, manual verification passed in full: POST /chat with no thread_id streamed multiple token-delta chunks (not one blocking reply) and returned a generated UUIDv7 in X-Thread-Id; a follow-up request reusing that thread_id correctly recalled and quoted the first turn's exact message, confirming SQLite-checkpointed multi-turn state works across separate requests.

### Completed - 2026-08-06T04:21:59Z - John Hoff

All Requirements met and Verification passed: pdm run pytest -q (771 passed, no network/API-key dependence), ruff check/format clean. Manual local run confirmed the full plumbing works end-to-end: POST /chat with no thread_id streamed multiple token-delta chunks (not one blocking reply) and returned a generated UUIDv7 in the X-Thread-Id header; a follow-up request reusing that thread_id correctly recalled and quoted the first turn's exact message, confirming SQLite-checkpointed multi-turn state persists across separate requests. Two environment-only issues (a malformed API key, then a rate-limited free model) were hit and resolved during manual verification per the prior log entry - no code changes resulted from either beyond the load_dotenv path fix already logged. Confirmed complete with the GM.
