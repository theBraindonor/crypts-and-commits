---
campaign: v0.1.0-bootstrapping
created_by: John Hoff
created_on: '2026-07-25T01:22:31Z'
name: 06-mcp-surface
regions:
- crypts-and-commits
status: draft
updated_by: John Hoff
updated_on: '2026-07-25T01:23:05Z'
---

# MCP Surface

## Requirements

- Wrap the core retrieval capabilities in the MCP server (the `mcp/` placeholder), exposing intent-based tools: context prime, applicable-lore, get, and list — reusing the same `core` logic the CLI calls (thin-wrapper rule).
- Apply the 20,000-character budget + prepended-truncation behavior (encounter 04) to MCP responses.
- Leave a slot for a `search` tool but do NOT implement it (encounter search is deferred; see `docs/encounter-search-design.md`).
- No domain logic in the MCP layer — it calls `core`, the same as the CLI.

## Rationale

Per `docs/context-management-design.md`, the MCP server is the eventual replacement for CLI shell-outs as the interaction layer, and the long-term goal is the agent having no awareness of `.sourcebook`'s existence. Building it as a thin wrapper over the same core capabilities (established in encounters 01-04) keeps a single source of truth and lets the CLI and MCP coexist during the transition.

## Plan

_To be finalized in draft._ Outline:
1. `mcp/`: implement the server exposing prime/applicable-lore/get/list tools over `core`.
2. Wire the budget/truncation serialization (encounter 04).
3. Leave the `search` tool slot unimplemented.
4. Tests as appropriate for the MCP layer.
5. `clean-tests-and-lint`.

## Verification

- `pdm run pytest -q` and `ruff check`/`format` clean.
- The MCP server exposes the intent-based tools, backed by `core`, with budget/truncation applied; no `search` tool yet.
