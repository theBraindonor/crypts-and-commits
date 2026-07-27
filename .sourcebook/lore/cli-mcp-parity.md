---
assigned_regions:
- crypts-and-commits
assigned_to_world: false
enabled: true
name: cli-mcp-parity
summary: 'Every CLI command must have a matching MCP tool in mcp/ (thin wrapper into
  core/, no CLI-only console/confirm/editor concerns), with cursor paging and body
  truncation preserved - except bootstrap and index rebuild, both permanently CLI-only
  since they''re developer-only maintenance operations. Purpose: let an agent fall
  back to the CLI when the MCP server isn''t available. Check this when any cli/ command
  changes.'
updated_by: John Hoff
updated_on: '2026-07-27T05:00:23Z'
---

# CLI/MCP Command Parity

Every command exposed by the `cac` CLI must have a corresponding MCP tool in
`mcp/`, with two permanent exceptions:

- `bootstrap` (`cac bootstrap init`) - never exposed via MCP, because it is
  developer-only per this project's guardrail - the assistant must never run
  it, over CLI or MCP.
- `index rebuild` (`cac index rebuild`) - never exposed via MCP. Rebuilding
  the search index from scratch is a heavier, manual maintenance operation
  meant to be triggered by the developer directly, not something an agent
  should be able to invoke on its own initiative via MCP. `cac index status`
  and `cac index search` are ordinary read operations and are not covered by
  this exception - they still require MCP parity like any other command.

The reason for this parity requirement: the MCP server is meant to be a normal,
but not the only, way to interact with `.sourcebook`. An agent must always be
able to fall back to the `cac` CLI directly when the MCP server is unavailable
or not configured for a session. If a command exists only over MCP (or only
over the CLI, aside from the two exceptions above), that fallback breaks.

When reviewing any encounter that adds or changes a `cac` CLI command in
`cli/`:
- Confirm the same command is added to (or already exists in) the matching
  `mcp/<domain>.py` module, following the existing thin-wrapper pattern (calls
  straight into `core/`, no CLI-only concerns like `rich` console output,
  `edit_markdown`, `typer.confirm`, or `fail()`/exit-code handling).
- CLI-only interactive affordances that don't translate to a single MCP call
  must be adapted, not silently dropped: `--yes/-y` confirmation becomes
  unconditional deletion in the MCP tool; the "open `$EDITOR` if body omitted"
  fallback becomes a required argument with no default.
- Paginated `list` commands and `encounter order` must expose the same
  cursor-based paging contract as the CLI (`budget_core.paginate`), returning
  structured data rather than printed lines. `get` commands must apply the
  same `budget_core.truncate_body` truncation.
- New domain modules must be wired into `mcp/server.py`'s `_TOOL_MODULES`, and
  `tests/mcp/test_server.py::test_all_domain_tools_are_registered` must be
  updated to reflect the new tool set.

If a new CLI command is added and this parity is not extended to cover it in
the same change, treat that as a lore violation unless the Plan explicitly
justifies the gap (e.g. a third `bootstrap`/`index rebuild`-like,
developer-only exception).
