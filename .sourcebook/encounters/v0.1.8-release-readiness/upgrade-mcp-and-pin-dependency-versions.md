---
archived: false
campaign: v0.1.8-release-readiness
created_by: John Hoff
created_on: '2026-08-06T15:48:26Z'
depends_on: []
name: upgrade-mcp-and-pin-dependency-versions
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-08-09T02:16:11Z'
---

# Upgrade to latest mcp and put better version pins in place

## Requirements

- `packages/crypts-and-commits/pyproject.toml` currently pins `mcp<2.0.0` as a stopgap (added during `v0.1.7-rag-demo-application`'s `add-chat-persona-and-context-priming` encounter, after an unpinned `mcp` dependency let a plain `pdm lock` silently jump from 1.28.1 to 2.0.0 and break `cac.mcp.instance`'s `from mcp.server.fastmcp import FastMCP` import). Upgrade `cac`'s MCP server code (`cac/mcp/instance.py`) to the `mcp` 2.x API and replace the stopgap with `mcp>=2.0.0,<3.0.0`.
- Beyond `mcp` specifically, audit the workspace's other unpinned or loosely-pinned direct dependencies (both `packages/crypts-and-commits/pyproject.toml` and `packages/demo-api/pyproject.toml`) and decide, package by package, on an explicit version constraint policy (e.g. lower-bound-only for libraries expected to be stable/additive, upper-bound or exact pins for anything with a track record of breaking majors) - this is release-readiness work, not just the `mcp` incident response.
- `pdm lock` must continue to resolve deterministically without unreviewed major-version jumps going forward; document (in this encounter's Verification, and/or as new `crypts-and-commits`-region lore if a durable convention emerges) what re-lock practice avoids repeating this - e.g. preferring `pdm lock --update-reuse` / reviewing `git diff pdm.lock` version-line changes before accepting a relock, over a bare `pdm lock`.
- All existing behavior must keep working: `pdm run pytest -q` and `pdm run ruff check .` / `ruff format .` clean, including the full `cac.mcp.*` test suite against `mcp` 2.0.0.

## Rationale

The `mcp<2.0.0` pin added during the persona/priming encounter was explicitly a stopgap ("stemming the bleeding," not a fix) - it stops the immediate breakage but leaves `cac`'s own MCP server pinned below the current upstream major release indefinitely, which isn't a sustainable position for a package heading toward its first public release (this campaign's stated purpose). Auditing and firming up dependency-version policy more broadly, while already in this territory, is cheaper to do now as one pass than to rediscover incident-by-incident later - and this campaign's body already calls out packaging/versioning strategy as a known candidate area to survey.

Pre-drafting investigation found `cac`'s actual surface against `mcp` is narrow: only `instance.py`'s `FastMCP(...)` construction, `@mcp.tool()` decorators across the 11 `cac/mcp/*` tool modules, `mcp.run()` (stdio, no transport kwargs), and `tests/mcp/test_server.py`'s `mcp.list_tools()` introspection call. `mcp` 2.0.0 (released 2026-07-28, the only 2.x release to date) renames `FastMCP` to `MCPServer` and moves it from `mcp.server.fastmcp` to `mcp.server.mcpserver`, but leaves the decorator API (`@mcp.tool()` et al.) and the `list_tools()`/`list_resources()`/`list_prompts()` introspection methods unchanged; `cac` passes only a single positional `name` to the constructor, unaffected by v2's positional-arg reordering; and v2's change to run sync tool handlers via `anyio.to_thread.run_sync()` is a non-issue since no `cac` code calls `asyncio.get_running_loop()` or otherwise assumes the event-loop thread (confirmed via grep: no `asyncio`/`async def` anywhere in `cac`'s source). Net expected code change is the two-line import/rename in `instance.py`, with no other `cac/mcp/*` module or the test suite expected to need edits.

Given that low cost, and that `mcp` 1.x is now maintenance-mode-only upstream, holding on 1.x would just recreate the same "pinned below current major indefinitely" problem this encounter exists to resolve. The user signed off on upgrading now over holding, on this basis.

## Plan

1. Update `cac/mcp/instance.py`'s import and constructor to `from mcp.server.mcpserver import MCPServer` / `MCPServer("crypts-and-commits")`; remove the `<2.0.0` upper bound from `packages/crypts-and-commits/pyproject.toml`, replacing it with `mcp>=2.0.0,<3.0.0`. If anything beyond `instance.py` turns out to need changes (contrary to the scoping in Rationale), record why via `encounter_record_message` before proceeding further.
2. Audit remaining direct dependencies in both `packages/crypts-and-commits/pyproject.toml` and `packages/demo-api/pyproject.toml`; apply the version-constraint policy decided in Requirements consistently across both.
3. Relock with `pdm lock --update-reuse` and review `git diff pdm.lock` for any unexpected version-line changes before accepting; run `pdm install`.
4. Run `pdm run pytest -q` and `pdm run ruff check .` / `pdm run ruff format .`; fix anything either surfaces.

## Verification

- `pdm run pytest -q` passes (no skips/deletions to dodge failures), including the full `cac.mcp.*` suite against `mcp` 2.0.0.
- `pdm run ruff check .` reports zero errors and `pdm run ruff format .` reports no diffs.
- `packages/crypts-and-commits/pyproject.toml` carries `mcp>=2.0.0,<3.0.0` in place of the old `mcp<2.0.0` stopgap.
- `git diff pdm.lock` for the final relock is reviewed line-by-line for version changes and confirmed to contain no unreviewed/unexplained major-version jumps.

## Log

### Review - 2026-08-09T01:49:47Z - John Hoff

Reviewed against all five applicable lore items. `clean-tests-and-lint` is directly honored by Plan step 4 and the Verification section. `cli-mcp-parity`, `console-best-practices`, and `skills-authored-only-in-templates` are not implicated since no CLI command, console-print, or skill-template changes are in scope. `workflow-doc-source-of-truth` is likely satisfied in substance — the Rationale argues persuasively that the `mcp` 2.x upgrade is a pure internal rename with no observable change to any exposed tool's behavior/name/args/return shape — but neither the Plan nor Verification explicitly confirms `workflow.md` needs no update, which would be worth a one-line addition for completeness. Separately, flagging (not blocking) that the encounter's Requirements bring `packages/demo-api/pyproject.toml` into scope for the dependency-pin audit while `regions` lists only `crypts-and-commits`; if a `demo-api` region with its own lore exists, it wasn't picked up by this review's lore resolution — worth confirming before proceeding. No lore conflicts found; recommend proceeding, optionally with the two notes above addressed.

### Message - 2026-08-09T01:53:04Z - John Hoff

Reviewer flagged that packages/demo-api/pyproject.toml is in Requirements scope while only the crypts-and-commits region is assigned. Checked demo-api's only assigned lore (demo-api-uses-cac-core-directly) — it governs how demo-api reads .sourcebook data, unrelated to dependency version pinning. User confirmed: proceed with auditing/updating demo-api's pins as originally planned; no region reassignment needed since no lore conflict exists.

### Message - 2026-08-09T02:08:29Z - John Hoff

Scope correction per user feedback: only mcp and tomlkit get an explicit version-constraint ceiling in packages/crypts-and-commits/pyproject.toml. typer, rich, click, and python-frontmatter are left as originally (unpinned) rather than pinned per the general policy applied earlier - crypts-and-commits is the only package intended for distribution, so its pin discipline should stay minimal to what's actually needed (mcp for the incident this encounter addresses, tomlkit which already carried a lower bound). packages/demo-api/pyproject.toml's pins are reverted entirely to their original state (lower-bound-only) and confirmed via git diff to show no changes, since the demo packages aren't distributed and don't need this treatment. Relocked (pdm lock --update-reuse), reviewed git diff pdm.lock (only mcp/mcp-types and their transitive tree changed, consistent with the mcp 2.0.0 upgrade - no other version movement), pdm install, and reran pdm run pytest -q (804 passed) and ruff check/format (both clean) against the narrowed pin set.

### Message - 2026-08-09T02:15:22Z - John Hoff

Further scope correction per user feedback: removed the <3.0.0 and <0.16.0 upper-bound ceilings on mcp and tomlkit in packages/crypts-and-commits/pyproject.toml. Final state: mcp>=2.0.0, tomlkit>=0.15.1 (lower-bound-only, tomlkit restored to its original constraint) - no explicit version-constraint policy beyond the mcp stopgap replacement itself. Relocked (pdm lock --update-reuse), reviewed git diff pdm.lock (only mcp/mcp-types and their transitive tree changed, same as prior passes - no other version movement), pdm install, and reran pdm run pytest -q (804 passed) and ruff check/format (both clean) against this final pin set.

### Completed - 2026-08-09T02:16:11Z - John Hoff

mcp upgraded to 2.x (FastMCP -> MCPServer rename in instance.py, mcp>=2.0.0 in pyproject.toml). Broader dependency-pin audit was scoped back per user feedback to just the mcp stopgap replacement - typer/rich/click/python-frontmatter/tomlkit stay as originally constrained, and demo-api's pins are untouched, since crypts-and-commits is the only package intended for distribution. pytest (804 passed) and ruff check/format clean on the final state.
