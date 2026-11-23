---
assigned_lore:
- demo-api-uses-cac-core-directly
name: demo-api
path: packages/demo-api
summary: 'Backend region packages/demo-api: FastAPI (/, /health, /docs) with streaming
  NDJSON POST /chat backed by a LangGraph tool-calling agent. CAC project-assistant
  persona plus live sourcebook priming (cac.core prime bundle) as literal system messages;
  read-only cac.core tools for world, lore, regions, campaigns, encounters, docs and
  index search. OpenRouter model (.env, default google/gemma-4-31b-it); optional thread_id
  (UUIDv7 via X-Thread-Id); SQLite checkpointer.'
updated_by: John Hoff
updated_on: '2026-11-23T18:44:54Z'
---

# Demo API (backend)

The backend of a demonstration web application showing off crypts-and-commits in action.

## Current state

- FastAPI app (`demo_api.main`): `GET /` (a small HTML index), `GET /health`, and Swagger UI at `/docs`.
- `POST /chat` streams the agent's reply as NDJSON (`application/x-ndjson`, one `{"content": ...}` object per chunk) from a LangGraph graph (`demo_api.chat.graph.build_graph`), built once at startup in the app lifespan.
- **Persona:** `graph.SYSTEM_PROMPT` makes the model the Crypts and Commits project assistant. It helps developers understand the project, answers questions about the current sourcebook (world context, lore, regions and campaigns), and prefers its tools over guessing when asked about live status.
- **Context priming:** `demo_api.chat.priming.render_context_priming` renders `cac.core.prime.assemble_prime` (world name and body, global lore summaries, the region map, and the active campaign body) into a second system message.
- **Prompt construction:** `_build_prompt` passes the persona and priming as literal `SystemMessage` entries, followed by the `messages` placeholder. Sourcebook text is never templated (c006/e002; see `demo-api-uses-cac-core-directly`).
- **Tools:** a tool-calling loop (`ToolNode` plus `tools_condition`) binds read-only `cac.core` tools from `demo_api.chat.tools`, registered in `_BUILDERS`: campaigns (`list_campaigns`, `get_campaign`), docs (`list_docs`, `get_doc`), encounters (`list_encounters`, `get_encounter`), lore (`list_lore`, `get_lore`), regions (`list_regions`, `get_region`), world (`get_world`) and `search_sourcebook` (full-text index search). Add a domain by adding a `build_tools(root)` module and appending it to `_BUILDERS`.
- **Consumer:** `demo-ui` reads the `/chat` NDJSON stream and carries the `X-Thread-Id` header forward as `thread_id` (see the `demo-ui` region).

## Confirmed technology decisions

- **LangGraph** (not a general-purpose LangChain agent) is the orchestration layer: a graph-based agent exposed via `POST /chat`, streaming output as it's generated rather than returning a single blocking response.
- **OpenRouter** is the model access layer: one API key covers many providers and models through an OpenAI-compatible endpoint (`langchain_openai.ChatOpenAI` with OpenRouter's base URL), rather than hard-coding to OpenAI or Anthropic directly.
- Model selection is configuration, not code. The OpenRouter API key and model id (`CHAT_MODEL`) are read from environment variables, loaded via **python-dotenv** from a `.env` file (gitignored, with a `.env.example` documenting the required keys). The model defaults to `google/gemma-4-31b-it`, the paid tier. The `:free` variant hit OpenRouter's shared rate limits too often during development to be reliable.
- `POST /chat` accepts an optional `thread_id`. When it's omitted, the API generates one (UUIDv7, via the `uuid6` package) and returns it in the `X-Thread-Id` response header, keeping id creation and format under the API's control.
- **LangGraph's SQLite checkpointer** (`AsyncSqliteSaver`, at `.data/chat.sqlite`) persists conversation state per `thread_id`, enabling real multi-turn conversations across separate requests.
- All sourcebook access goes through read-only `cac.core` calls, never the CLI or MCP (`demo-api-uses-cac-core-directly`).

## Still to confirm

- Whether retrieval needs anything beyond the agent's `search_sourcebook` tool and context priming (e.g. dedicated RAG retrieval steps).

## Status

The chat agent works end to end: persona, live sourcebook priming, read-only sourcebook tools, streaming and SQLite checkpointing, consumed by demo-ui. Treat anything under "Still to confirm" as unsettled, and confirm with the user before assuming details not yet reflected in code.
