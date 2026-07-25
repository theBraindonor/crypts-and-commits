---
campaign: v0.1.1-mcp-transition
created_by: John Hoff
created_on: '2026-07-25T21:01:39Z'
depends_on: []
name: expand-mcp-server-to-lore-region-campaign-encounter
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-07-25T21:14:19Z'
---

# Encounter

## Requirements

- Add MCP tool coverage for every `cac` CLI command not yet exposed via MCP,
  across the four remaining domains: `lore`, `region`, `campaign`, and
  `encounter`. `world` and `prime` are already done (`mcp/world.py`,
  `mcp/prime.py`). `bootstrap` is explicitly and permanently out of scope: it
  is developer-only per CLAUDE.md's guardrail (the assistant must never run
  `cac bootstrap init`), so it must never be exposed as an MCP tool either —
  call this out so a future contributor doesn't "complete the set" by adding
  it. Once this encounter is done, every CLI command except `bootstrap`'s is
  available over MCP.
- Each new MCP module (`mcp/lore.py`, `mcp/region.py`, `mcp/campaign.py`,
  `mcp/encounter.py`) must follow the existing `mcp/world.py` / `mcp/prime.py`
  pattern: thin `@mcp.tool()`-decorated functions that call straight into the
  matching `core` module and return JSON-serializable dicts/lists. No
  CLI-only concerns may leak into the MCP layer: no `rich` console output, no
  `edit_markdown` editor fallback, no `typer.confirm` interactive prompts, no
  `fail()` / non-zero-exit handling. Exceptions propagate directly to the
  caller, matching the existing `test_world_get_missing_world_raises`
  pattern, rather than being caught and turned into a printed message.
- Two CLI affordances don't translate to a single MCP call and must be
  adapted rather than silently dropped:
  - `delete` commands' `--yes/-y` confirmation skip has no console to confirm
    against in an MCP tool call — the MCP `delete` tools must delete
    unconditionally (equivalent to always passing `--yes`).
  - `create`/`update` commands' "open `$EDITOR` if body omitted" fallback
    doesn't apply either — the MCP versions must require the body argument
    outright, with no default and no editor fallback.
- Paginated `list` commands (lore/region/campaign/encounter) must expose the
  same cursor-based paging contract the CLI already has via
  `budget_core.paginate`, returning structured data — e.g.
  `{"items": [...], "next_cursor": str | None}` — rather than pre-rendered
  console lines. `encounter order` similarly returns structured
  name/status/depends_on entries rather printed lines.
- `get` commands must apply the same `budget_core.truncate_body` truncation
  the CLI applies to long bodies, for the same context-budget reason the
  CLI's pagination and truncation already exist.
- `encounter` tools must support the same campaign-defaulting behavior the
  CLI has (`campaign_core.resolve_campaign`, defaulting to the active/open
  campaign when omitted), matching how `mcp/prime.py`'s
  `prime_applicable_lore` already does this.
- Every new tool function needs a docstring — FastMCP surfaces it as the
  tool's description — written in the same voice and level of detail as the
  existing `world_get` / `prime_get` / `prime_applicable_lore` docstrings.
- `mcp/server.py`'s `_TOOL_MODULES` tuple must be extended to import each new
  domain module (for its `@mcp.tool()` registration side effects), and
  `tests/mcp/test_server.py`'s `test_all_domain_tools_are_registered` must be
  updated to assert the complete tool-name set across all six modules.
- No changes to `core/` or the existing `cli/` modules are in scope — this
  encounter only adds a new MCP-facing layer on top of already-existing,
  already-tested `core` functions.

## Rationale

The active campaign (`v0.1.1-mcp-transition`) exists to move `.sourcebook`
interaction from CLI shell-outs to an MCP server, working toward the
framework's stated end-state: the coding assistant should have no awareness
of the `.sourcebook` directory's existence at all. Two prior encounters
(`build-mcp-server-world-and-prime-tools`,
`split-mcp-server-into-domain-modules`) stood up the server and covered the
`world` and `prime` domains. This encounter is the next major step: closing
out `lore`, `region`, `campaign`, and `encounter` so that, once complete,
`bootstrap` is the *only* command family left CLI-only — and that's by
design, not an oversight, since bootstrap is developer-only. It sets up a
later encounter (not this one) to migrate the `world-manager` /
`campaign-manager` skills themselves to call the MCP tools instead of
shelling out to `cac`.

## Plan

1. Add `mcp/lore.py` with tools for `get`, `list`, `create`, `update`,
   `delete`, `set-summary`, `assign-world`, `unassign-world`,
   `assign-region`, `unassign-region`, `enable`, `disable` — mirroring
   `cli/lore.py`'s command set, adapted per the Requirements above (no
   confirm, no editor fallback, budget truncation on `get`, structured
   paging on `list`).
2. Add `mcp/region.py` with tools for `get`, `list`, `create`, `update`,
   `delete`, `set-summary`, `set-path` — mirroring `cli/region.py`.
3. Add `mcp/campaign.py` with tools for `get`, `list`, `create`, `update`,
   `delete`, `open`, `pause`, `complete`, `abandon` — mirroring
   `cli/campaign.py`.
4. Add `mcp/encounter.py` with tools for `get`, `list`, `order`, `create`,
   `update`, `delete`, `review`, `open`, `record-message`, `complete`,
   `abandon`, `assign-region`, `unassign-region`, `assign-dependency`,
   `unassign-dependency` — mirroring `cli/encounter.py`, including the
   campaign-defaulting behavior via `campaign_core.resolve_campaign`.
5. Settle on one consistent paginated-list return shape (e.g. `{"items":
   [...], "next_cursor": str | None}`) and reuse it across all four new
   modules' `list` tools, built on top of `budget_core.paginate`.
6. Wire all four new modules into `mcp/server.py`'s `_TOOL_MODULES`.
7. Update `tests/mcp/test_server.py` to assert the full six-module tool set.
8. Add `tests/mcp/test_lore.py`, `test_region.py`, `test_campaign.py`, and
   `test_encounter.py`, mirroring `test_world.py`'s fixture pattern
   (`tmp_path`-as-cwd, `git_utils.current_git_user` patched), each covering
   at minimum one happy path per tool plus the not-found/error case
   propagating as a raised exception.

## Verification

- `pdm run pytest -q` passes, including the four new `tests/mcp/` modules.
- `pdm run ruff check .` and `pdm run ruff format .` are clean, per the
  `clean-tests-and-lint` world lore.
- `test_all_domain_tools_are_registered` lists every tool across all six
  modules (`world`, `prime`, `lore`, `region`, `campaign`, `encounter`) and
  confirms no bootstrap-related tool is present.
- Manually confirm the full tool roster via `asyncio.run(mcp.list_tools())`
  (or the running `cac-mcp` server) matches the CLI's command surface minus
  `bootstrap`.

## Log

### Review - 2026-07-25T21:04:13Z - John Hoff

Reviewed against the one lore item currently in scope (clean-tests-and-lint, world-assigned): the Plan's Verification section explicitly requires pdm run pytest -q and clean ruff check/ruff format, satisfying it directly. Note: this encounter has no assigned regions despite all planned changes living under packages/crypts-and-commits, so the crypts-and-commits region's console-best-practices lore was never pulled into this review - the Plan appears to satisfy it in substance (no rich console output planned for the MCP layer, core logic stays in core/), but consider assigning that region so future review of this work goes through the formal gate rather than an incidental match. No conflicts found; passing with that note.

### Completed - 2026-07-25T21:14:19Z - John Hoff

Added mcp/lore.py, mcp/region.py, mcp/campaign.py, mcp/encounter.py mirroring the world/prime thin-wrapper pattern; wired into server.py's _TOOL_MODULES. Verification passed: pdm run pytest -q (563 passed), ruff check and ruff format clean, and a live tool-roster check confirming 48 tools registered with zero bootstrap-related tools. Manually re-verified against a running session after restart - all new tools load and lore_list returned real data.
