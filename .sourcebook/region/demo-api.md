---
name: demo-api
path: packages/demo-api
summary: Backend region packages/demo-api. FastAPI shell (/, /health, /docs) and streaming
  POST /chat (LangGraph, plumbing only) exist. Model via OpenRouter (.env, default
  google/gemma-4-31b-it - :free tier dropped, frequent rate limits). Optional thread_id;
  server generates UUIDv7 via X-Thread-Id header if omitted. Multi-turn via SQLite
  checkpointer; ChatPromptTemplate, system prompt "You are a friendly assistant."
  RAG, tools, demo-ui integration unconfirmed.
updated_by: John Hoff
updated_on: '2026-08-06T04:24:22Z'
---

# Demo API (backend)

The backend of a demonstration web application showing off crypts-and-commits in action.

## Current state

- FastAPI app shell exists (`bootstrap-fastapi-app-shell` encounter): `GET /`, `GET /health`, Swagger UI at `/docs`.
- A streaming `POST /chat` endpoint wired to a LangGraph agent exists (`add-streaming-chat-endpoint` encounter): plumbing only (no RAG, no tools yet) - see "Confirmed technology decisions" below.
- No RAG/tool-calling functionality yet - see "Still to confirm".

## Confirmed technology decisions

- **LangGraph** (not a general-purpose LangChain agent) is the orchestration layer - a graph-based agent exposed via `POST /chat`, streaming output as it's generated rather than returning a single blocking response.
- **OpenRouter** is the model access layer - one API key covers many providers/models through an OpenAI-compatible endpoint, rather than hard-coding to OpenAI or Anthropic directly.
- Model selection is configuration, not code: the OpenRouter API key and model id are read from environment variables, loaded via **python-dotenv** from a `.env` file (gitignored, with a `.env.example` documenting the required keys). The model defaults to `google/gemma-4-31b-it` (the paid tier) - the `:free` variant was tried first but hit OpenRouter's shared rate limits often enough during development to be unreliable for local dev.
- `POST /chat` accepts an optional `thread_id`; when omitted the API generates one (UUIDv7, via the `uuid6` package) and returns it in the `X-Thread-Id` response header, keeping id creation/format under the API's control.
- **LangGraph's SQLite checkpointer** persists conversation state per `thread_id`, enabling real multi-turn conversations across separate requests.
- A standard chat-prompt structure (system prompt + conversation history + new human turn, via `ChatPromptTemplate`) backs the agent, starting from the system prompt "You are a friendly assistant." Tool calling is expected to be layered on top of this graph incrementally, not built out yet.
- Retrieval (RAG grounded in `.sourcebook`) is still planned but was explicitly out of scope for the initial `/chat` wiring - that work was deliberately plumbing-only: LangGraph + OpenRouter + FastAPI + streaming connected end-to-end, before the agent's actual answers are made to depend on `.sourcebook` content.

## Still to confirm

- The RAG retrieval mechanism into `.sourcebook` content (via `cac`/`index_search`, not raw markdown parsing) - not yet wired into the agent.
- Tool-calling specifics once introduced.
- How `demo-ui` consumes the `/chat` endpoint's streaming response - not yet designed.

## Status

`/chat` plumbing (LangGraph + OpenRouter + SQLite checkpointing + streaming) is done. Treat anything under "Still to confirm" as unsettled - confirm with the user before assuming implementation details not yet reflected in code.
