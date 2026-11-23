---
assigned_regions:
- crypts-and-commits
assigned_to_world: false
enabled: true
name: cli-mcp-parity
summary: Every CLI command needs a matching MCP tool in mcp/ (thin wrapper into core/,
  no CLI-only console/confirm/editor concerns) with the same cursor paging and get-body
  continuation, except permanently CLI-only bootstrap and index rebuild. New or changed
  MCP pages must fit the budget as emitted (compact JSON plus envelope, one core helper
  shared with the CLI). Descriptions agree across MCP/CLI, render as clean prose,
  never exceed tool-reference.md's specificity; enumerated sets get drift-guard tests.
updated_by: John Hoff
updated_on: '2026-11-23T18:14:10Z'
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
  structured data rather than printed lines. `get` commands must fit their
  result through the shared `budget_core.fit_response` helper and accept the
  same `cursor`/`--cursor` continuation; a truncation notice must never point
  at a file.
- When adding or changing a paged MCP result, every page must fit the response
  budget as emitted. Size each item as its compact JSON and reserve the full
  result envelope, including `next_cursor` and any field the
  `references.inputs` decorator adds (such as `identity`). Share one `core/`
  paging helper between the MCP tool and the CLI command so both break pages
  at the same entries. The only allowed overrun is a single item that alone
  exceeds the budget (`paginate` always admits one item).
- New domain modules must be wired into `mcp/server.py`'s `_TOOL_MODULES`, and
  `tests/mcp/test_server.py::test_all_domain_tools_are_registered` must be
  updated to reflect the new tool set.

If a new CLI command is added and this parity is not extended to cover it in
the same change, treat that as a lore violation unless the Plan explicitly
justifies the gap (e.g. a third `bootstrap`/`index rebuild`-like,
developer-only exception).

## Description accuracy

Parity covers the descriptions agents read, not only command existence. An MCP
tool description and its CLI help must agree on every fact either states
(statuses, guards, filter values, defaults), and `tool-reference.md` must be at
least as specific: a fact stated in a description is stated in the owning
contract too. Where a description enumerates a set defined in code (object
types, statuses, registered docs), add a drift-guard test deriving the expected
values from config or the registry, never hard-coded and never asserting prose
wording. Drift guards cover names only; prose accuracy relies on review.

Descriptions must also render as clean prose, with no indentation or space
runs. MCP tools register only through the shared `mcp` instance in
`mcp/instance.py`, which cleans docstrings (the SDK passes them verbatim), and
any text appended to a docstring (e.g. the `references.inputs` contract footer)
goes after `inspect.cleandoc`, never before. Whitespace guards in
`tests/mcp/test_server.py` and `tests/cli/test_app.py` cover every tool and
command; fix flagged text, never loosen them.
