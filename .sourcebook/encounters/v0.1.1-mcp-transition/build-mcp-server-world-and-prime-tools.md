---
campaign: v0.1.1-mcp-transition
created_by: John Hoff
created_on: '2026-07-25T20:09:44Z'
depends_on: []
name: build-mcp-server-world-and-prime-tools
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-07-25T20:28:02Z'
---

## Requirements

- A new `cac.mcp` module (`packages/crypts-and-commits/src/cac/mcp/`) that runs an MCP server over
  stdio, built on the official `mcp` Python SDK (`FastMCP`).
- A `cac-mcp` console script, registered in `packages/crypts-and-commits/pyproject.toml`
  `[project.scripts]` alongside the existing `cac` entry, installed into `.venv` the same way via
  `pdm install` - no separate install step.
- Initial tool surface limited to the `world` and `prime` core modules only:
  - `world`: `get`, `set` (attribute), `set_body`.
  - `prime`: `get`, `applicable_lore`.
  - Everything else (`lore`, `region`, `campaign`, `encounter`, `bootstrap`) is explicitly out of
    scope for this encounter - confirmed with the user before starting.
- `cac bootstrap init` writes (or merges into) a `.mcp.json` at the project root registering the
  `cac-mcp` server, resolving the actual installed script's path rather than assuming it is on
  `PATH` (mirrors the "`cac` is only on PATH via `pdm run cac`" wrinkle noted in this repo's own
  CLAUDE.md).
- Core exceptions (e.g. `WorldNotFoundError`) surface as MCP tool errors, not uncaught server
  crashes.
- Tests under `packages/crypts-and-commits/tests/mcp/`, mirroring the new `src/cac/mcp/` module per
  this repo's "tests mirror src" convention.

## Rationale

This is the first concrete step of the already-open `v0.1.1-mcp-transition` campaign: build an MCP
server exposing the same domain operations as the CLI, ahead of migrating the `world-manager`/
`campaign-manager` skills to call it instead of shelling out to `cac`. Per the user's explicit
direction, scope is deliberately narrowed to `world` + `prime` first, to get one operating,
end-to-end server (SDK wiring, console-script packaging, and the bootstrap path-resolution problem)
proven before multiplying the same pattern across every other domain module. `core/` already fully
separates domain logic from CLI presentation (`cac/cli/` modules are documented as thin wrappers
only), so `cac.mcp` tools can call `cac.core.world` / `cac.core.prime` directly with no changes
needed to `core` itself.

## Plan

1. Add `mcp` (the official MCP Python SDK) as a dependency of `packages/crypts-and-commits` in its
   `pyproject.toml`; run `pdm lock` and `pdm install` to pick it up in `.venv`.
2. Build out `cac/mcp/` (currently only an empty `__init__.py`):
   - `server.py`: construct a `FastMCP` instance and register tools that call directly into
     `cac.core.world` / `cac.core.prime`, using `Path.cwd()` as root (matching the CLI's existing
     convention). Translate core exceptions into MCP tool-level errors instead of letting them
     crash the process. Expose a `main()` entry point that runs the server over stdio transport.
3. Register the console script: add `cac-mcp = "cac.mcp.server:main"` under `[project.scripts]` in
   `packages/crypts-and-commits/pyproject.toml`.
4. Extend bootstrap (`core/bootstrap.py` + `cli/bootstrap.py`) to also write/merge a `.mcp.json` at
   the project root:
   - Resolve the installed `cac-mcp` script's absolute path from the running interpreter's own
     install location (its Scripts/bin sibling directory), rather than assuming `PATH`.
   - If `.mcp.json` already exists, merge the `cac` server entry into its `mcpServers` map instead
     of overwriting the file.
5. Add tests under `packages/crypts-and-commits/tests/mcp/` covering the new tool wrappers (success
   and translated-error cases) and bootstrap tests covering `.mcp.json` creation plus merge-into-
   existing-file behavior.

## Verification

- `pdm install` succeeds and installs the new `mcp` dependency and the `cac-mcp` script into
  `.venv`.
- `pdm run cac-mcp` starts the server without error; manually verify it is usable as a real MCP
  server (e.g. wired into a scratch project's `.mcp.json` and listed/callable from a client) and
  that the `world`/`prime` tools return the same information as their CLI equivalents.
- `pdm run cac bootstrap init` in a scratch directory produces a `.mcp.json` pointing at a real,
  executable `cac-mcp` path; re-running it against an existing `.mcp.json` that already has
  unrelated entries preserves those entries.
- `pdm run pytest -q` passes; `pdm run ruff check .` and `pdm run ruff format .` are clean, per the
  `clean-tests-and-lint` world lore.

## Log

### Review - 2026-07-25T20:12:47Z - John Hoff

Plan reviewed against applicable lore: clean-tests-and-lint is explicitly satisfied via the Verification section (pytest + ruff gates cited by name, no skip/suppression workarounds proposed). console-best-practices is not violated - its stated scope is rich.Console usage in cac/cli/*, and this Plan's new cac/mcp/server.py bypasses cli/ to call core.world/core.prime directly, returning results via the MCP protocol rather than rich.Console - but the Plan doesn't explicitly confirm that stored body content (world/lore/prime bodies, which have previously broken due to bracket-stripping under markup=True) will be returned to MCP clients as raw, unprocessed strings. Recommend the implementer note this explicitly so the same class of silent-content-loss bug doesn't reappear on the new server surface. No blocking conflicts found; approved to proceed.

### Completed - 2026-07-25T20:28:02Z - John Hoff

Verification passed: pdm run pytest -q (520 passed) and ruff check/format clean. End-to-end smoke test spawned the real cac-mcp.exe over stdio via the official MCP client, listing and calling world_get/prime_applicable_lore successfully, including a confirmed error path (isError: True without crashing the server). Independently confirmed by a separate Claude Code session connecting to and successfully calling the cac-mcp server. Scope was limited to world + prime tools per plan; remaining CLI domains (lore, region, campaign, encounter, bootstrap) are follow-up encounters.
