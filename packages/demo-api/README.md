# demo-api

A demonstration FastAPI backend for [Crypts and Commits](../../README.md)
(CAC). It serves a streaming chat agent that answers questions about *this
repository* — grounded in its own live `.sourcebook` content (world, lore,
regions, campaigns, encounters) and packaged docs — rather than a generic
chatbot. It exists to show `cac` used by ordinary, non-`cac` application code
in the same workspace: `demo-api` depends on `crypts-and-commits` and calls
`cac.core.*` directly (never the CLI as a subprocess, never MCP), and stays
strictly read-only against `.sourcebook` by construction — the same
functions the CLI and MCP server themselves wrap, never anything that writes.

## How it works

- **FastAPI** app (`demo_api.main`) exposing `GET /`, `GET /health`, Swagger
  UI at `/docs`, and a streaming `POST /chat`.
- **LangGraph** orchestrates the agent as a small graph (chat node ⇄ tool
  node) rather than a single blocking call; `POST /chat` streams tokens back
  as newline-delimited JSON as they're generated.
- **OpenRouter** (via `langchain-openai`'s `ChatOpenAI`) is the model access
  layer, so the backing model is a config choice, not a code change.
- **Multi-turn conversation** is kept per `thread_id` using LangGraph's SQLite
  checkpointer (`packages/demo-api/.data/chat.sqlite`, created on first run).
  `thread_id` is optional on `POST /chat` — omit it and the server generates
  one (UUIDv7) and returns it in the `X-Thread-Id` response header.
- **Grounding**: the agent's system prompt is primed with this repository's
  world/lore/region/active-campaign context at startup, and it's given a set
  of read-only tools — spanning campaigns, encounters, world, lore, regions,
  full-text sourcebook search, and packaged docs — that let it look up live
  status instead of guessing.

## Running it

From the repository root:

```bash
pdm install
```

`demo-api` calls an LLM through [OpenRouter](https://openrouter.ai/keys), so
it needs an API key:

```bash
cp packages/demo-api/.env.example packages/demo-api/.env
# then edit packages/demo-api/.env and set OPENROUTER_API_KEY
```

Then start the server:

```bash
pdm run uvicorn demo_api.main:app --app-dir packages/demo-api/src --reload
```

Serves on http://localhost:8000 — Swagger UI at `/docs`, health check at
`/health`. Pair it with [`demo-ui`](../demo-ui/README.md) for a full chat
frontend, or drive `/chat` directly (see `/docs` for the request/response
shape).

## Testing

From the repository root:

```bash
pdm run pytest packages/demo-api -q
```

## Learn more

- [Root repository README](../../README.md) — what Crypts and Commits is and
  how this package fits into the workspace.
- [`demo-ui`](../demo-ui/README.md) — the chat frontend for this API.
