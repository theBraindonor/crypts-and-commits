---
archived: false
campaign: v0.1.8-release-readiness
created_by: John Hoff
created_on: '2026-08-06T15:48:26Z'
depends_on: []
name: upgrade-mcp-and-pin-dependency-versions
regions: []
status: draft
updated_by: John Hoff
updated_on: '2026-08-06T15:48:26Z'
---

# Upgrade to latest mcp and put better version pins in place

## Requirements

- `packages/crypts-and-commits/pyproject.toml` currently pins `mcp<2.0.0` as a stopgap (added during `v0.1.7-rag-demo-application`'s `add-chat-persona-and-context-priming` encounter, after an unpinned `mcp` dependency let a plain `pdm lock` silently jump from 1.28.1 to 2.0.0 and break `cac.mcp.instance`'s `from mcp.server.fastmcp import FastMCP` import - confirmed by inspecting the 2.0.0 wheel directly: `fastmcp` is absent from it entirely). This encounter must properly resolve that stopgap: either upgrade `cac`'s MCP server code (`mcp/` subpackage, primarily `cac/mcp/instance.py` and anything else touching the `mcp.server.fastmcp` API) to work against the current `mcp` 2.x release, or make a deliberate, documented decision to stay on `mcp` 1.x for a stated reason - not just leave the 2.0.0 upper bound in place indefinitely by default.
- Beyond `mcp` specifically, audit the workspace's other unpinned or loosely-pinned direct dependencies (both `packages/crypts-and-commits/pyproject.toml` and `packages/demo-api/pyproject.toml`) and decide, package by package, on an explicit version constraint policy (e.g. lower-bound-only for libraries expected to be stable/additive, upper-bound or exact pins for anything with a track record of breaking majors) - this is release-readiness work, not just the `mcp` incident response.
- `pdm lock` must continue to resolve deterministically without unreviewed major-version jumps going forward; document (in this encounter's Verification, and/or as new `crypts-and-commits`-region lore if a durable convention emerges) what re-lock practice avoids repeating this - e.g. preferring `pdm lock --update-reuse` / reviewing `git diff pdm.lock` version-line changes before accepting a relock, over a bare `pdm lock`.
- All existing behavior must keep working: `pdm run pytest -q` and `pdm run ruff check .` / `ruff format .` clean, including the full `cac.mcp.*` test suite against whatever `mcp` version this encounter lands on.

## Rationale

The `mcp<2.0.0` pin added during the persona/priming encounter was explicitly a stopgap ("stemming the bleeding," not a fix) - it stops the immediate breakage but leaves `cac`'s own MCP server pinned below the current upstream major release indefinitely, which isn't a sustainable position for a package heading toward its first public release (this campaign's stated purpose). Auditing and firming up dependency-version policy more broadly, while already in this territory, is cheaper to do now as one pass than to rediscover incident-by-incident later - and this campaign's body already calls out packaging/versioning strategy as a known candidate area to survey.

## Plan

1. Read `cac/mcp/instance.py` and every other `cac/mcp/*` module against `mcp` 2.x's actual current API (start from the 2.0.0 wheel's `mcp/server/` layout, then check for any later 2.x releases) to scope what changed for `FastMCP` construction/registration and anything else `cac` depends on.
2. Decide and record (in this encounter, before writing code) whether to upgrade to `mcp` 2.x now or deliberately hold on 1.x with a stated reason - get the user's sign-off on that decision before proceeding, since it determines the rest of this encounter's shape.
3. If upgrading: update `cac/mcp/*` for the 2.x API, remove the `<2.0.0` upper bound (replacing it with whatever floor/ceiling the new policy below calls for), relock, and get the full suite green. If holding on 1.x: replace the ad hoc `<2.0.0` bound with an intentional constraint (e.g. `>=1.28,<2.0.0` with a comment/lore entry explaining why), and open a tracked follow-up for the eventual 2.x migration rather than leaving it implicit.
4. Audit remaining direct dependencies in both `packages/crypts-and-commits/pyproject.toml` and `packages/demo-api/pyproject.toml`; apply the version-constraint policy decided in Requirements consistently across both.
5. Relock with `pdm lock --update-reuse` and review `git diff pdm.lock` for any unexpected version-line changes before accepting; run `pdm install`.
6. Run `pdm run pytest -q` and `pdm run ruff check .` / `pdm run ruff format .`; fix anything either surfaces.

## Verification

- `pdm run pytest -q` passes (no skips/deletions to dodge failures), including the full `cac.mcp.*` suite against the landed `mcp` version.
- `pdm run ruff check .` reports zero errors and `pdm run ruff format .` reports no diffs.
- `packages/crypts-and-commits/pyproject.toml` no longer carries the bare `mcp<2.0.0` stopgap pin without explanation - either it's gone (upgraded) or replaced with an intentional, documented constraint.
- `git diff pdm.lock` for the final relock is reviewed line-by-line for version changes and confirmed to contain no unreviewed/unexplained major-version jumps.
