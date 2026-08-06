---
assigned_regions:
- demo-api
assigned_to_world: false
created_by: John Hoff
created_on: '2026-08-06T14:58:29Z'
enabled: true
name: demo-api-uses-cac-core-directly
summary: 'When demo-api needs sourcebook data (chat context priming, future RAG retrieval),
  it depends on crypts-and-commits and calls cac.core.* functions directly (e.g. cac.core.prime.assemble_prime)
  — never the cac CLI as a subprocess or the MCP server. The .sourcebook-is-MCP/CLI-only
  guardrail governs coding-assistant sessions, not same-workspace application code
  doing in-process reads. demo-api stays read-only: only non-mutating core calls,
  never writes.'
updated_by: John Hoff
updated_on: '2026-08-06T14:58:31Z'
---

# `demo-api` calls `cac.core` directly, not the CLI or MCP surface

`packages/demo-api` is ordinary Python application code that happens to live in the same PDM workspace as `crypts-and-commits` — it is not a coding-assistant session. When `demo-api` needs read-only sourcebook data (world/lore/region/campaign content — e.g. the chat agent's context priming, or future RAG retrieval via `index_search`), it must depend on `crypts-and-commits` as a normal Python dependency and call directly into `cac.core.*` functions (e.g. `cac.core.prime.assemble_prime`) — the same functions the CLI (`cli/`) and MCP server (`mcp/`) each wrap as thin layers over `core/`.

It must never shell out to the `cac` CLI as a subprocess, and never speak the MCP protocol to reach the same data:

- The `.sourcebook`-is-MCP/CLI-only guardrail (see `CLAUDE.md`) governs how a *coding-assistant session* touches `.sourcebook` at arm's length. It does not apply to ordinary application code performing an in-process library call in the same workspace — routing `demo-api` through the CLI or MCP anyway would only add subprocess/protocol overhead for no guardrail benefit.
- `core/` is the project's single source of truth; the CLI and MCP server are equally thin wrappers over it, never the other way around. `demo-api` reading `core` directly is consistent with that architecture, not a bypass of it.

This lore applies to any `demo-api` functionality that reads `.sourcebook` content, not just the initial chat persona/priming work.

`demo-api` remains read-only against `.sourcebook`: it may only call non-mutating `core` functions (reads/queries) — never anything that writes. The wider RAG-demo campaign requires the application to have no ability to write to `.sourcebook`, by construction, not just by convention.
