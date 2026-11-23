---
assigned_regions:
- demo-api
assigned_to_world: false
created_by: John Hoff
created_on: '2026-08-06T14:58:29Z'
enabled: true
name: demo-api-uses-cac-core-directly
summary: 'demo-api reads sourcebook data (context priming, chat tools, future RAG)
  by calling cac.core.* directly as a Python dependency - never the cac CLI as a subprocess
  or the MCP server; the MCP/CLI-only guardrail governs assistant sessions, not in-process
  app reads. Read-only: only non-mutating core calls. Sourcebook text is data: pass
  it to the model as literal messages (e.g. SystemMessage), never through prompt templating,
  which parses braces as variables.'
updated_by: John Hoff
updated_on: '2026-11-23T18:14:16Z'
---

# `demo-api` calls `cac.core` directly, not the CLI or MCP surface

`packages/demo-api` is ordinary Python application code that happens to live in the same PDM workspace as `crypts-and-commits` — it is not a coding-assistant session. When `demo-api` needs read-only sourcebook data (world/lore/region/campaign content — e.g. the chat agent's context priming, or future RAG retrieval via `index_search`), it must depend on `crypts-and-commits` as a normal Python dependency and call directly into `cac.core.*` functions (e.g. `cac.core.prime.assemble_prime`) — the same functions the CLI (`cli/`) and MCP server (`mcp/`) each wrap as thin layers over `core/`.

It must never shell out to the `cac` CLI as a subprocess, and never speak the MCP protocol to reach the same data:

- The `.sourcebook`-is-MCP/CLI-only guardrail (see `CLAUDE.md`) governs how a *coding-assistant session* touches `.sourcebook` at arm's length. It does not apply to ordinary application code performing an in-process library call in the same workspace — routing `demo-api` through the CLI or MCP anyway would only add subprocess/protocol overhead for no guardrail benefit.
- `core/` is the project's single source of truth; the CLI and MCP server are equally thin wrappers over it, never the other way around. `demo-api` reading `core` directly is consistent with that architecture, not a bypass of it.

This lore applies to any `demo-api` functionality that reads `.sourcebook` content, not just the initial chat persona/priming work.

`demo-api` remains read-only against `.sourcebook`: it may only call non-mutating `core` functions (reads/queries) — never anything that writes. The wider RAG-demo campaign requires the application to have no ability to write to `.sourcebook`, by construction, not just by convention.

## Sourcebook text is data, not a prompt template

Sourcebook content (context priming, tool results, future retrieval) must reach the chat model literally. Never pass it through prompt templating, such as a `("system", text)` tuple in `ChatPromptTemplate.from_messages`, which parses `{...}` as variables. Wrap it in a message object such as `SystemMessage(content=...)` instead. Sourcebook text routinely contains braces (e.g. `{items, next_cursor}`), and templating it either fails when the prompt is built or silently substitutes content.
