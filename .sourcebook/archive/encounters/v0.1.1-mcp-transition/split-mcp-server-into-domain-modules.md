---
archived: true
campaign: v0.1.1-mcp-transition
created_by: John Hoff
created_on: '2026-07-25T20:37:15Z'
depends_on: []
name: split-mcp-server-into-domain-modules
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-08-02T22:11:30Z'
---

## Requirements

- Split the existing `cac.mcp.server` module's `world`/`prime` tool functions out into their own
  files under `cac/mcp/`, one module per domain - mirroring how `cac/cli/` splits into one Typer
  sub-app per domain module.
- Each domain module (`cac/mcp/world.py`, `cac/mcp/prime.py`) owns its tool functions (unchanged
  behavior/signatures/docstrings from the current `server.py`) plus a `register(mcp: FastMCP) ->
  None` function that attaches its tools to a passed-in `FastMCP` instance via `mcp.add_tool(...)`.
- `cac/mcp/server.py` is reduced to: constructing the shared `FastMCP("cac")` instance, calling each
  domain module's `register(mcp)`, and the `main()` stdio entry point - no tool logic of its own.
- No behavior change: the same five tools (`world_get`, `world_set`, `world_set_body`, `prime_get`,
  `prime_applicable_lore`) with the same names, signatures, and outputs.
- Tests mirror the new layout: split `tests/mcp/test_server.py` into `tests/mcp/test_world.py` and
  `tests/mcp/test_prime.py` (per-domain tool behavior, same cases as today), plus a thin
  `tests/mcp/test_server.py` that checks composition - both domains' tools are actually registered
  on the shared instance (analogous to `tests/cli/test_app.py` checking each sub-app is wired up).
- This is a pure refactor to prepare for four more domains (`lore`, `region`, `campaign`,
  `encounter`) planned as later encounters - no new tools are added here.

## Rationale

The user is about to add four more CLI-mirroring domains to the MCP server; a single, growing
`server.py` would become unwieldy the same way a single monolithic CLI module would have. `cac/cli/`
already established the "one module per domain, composed in `app.py`" pattern for exactly this
reason, and `cac/core/` mirrors it too - `cac/mcp/` should follow the same convention rather than
inventing a different shape for the same problem. The official MCP Python SDK's `FastMCP` has no
`add_typer`-equivalent sub-router/mount mechanism (tool names stay flat across the whole server,
which is why they're already prefixed like `world_get`/`prime_get`), so composition here is a
lighter-weight `register(mcp) -> None` hook per module rather than a nested-app one - the closest
available analogue, agreed with the user before drafting this plan.

## Plan

1. Create `cac/mcp/world.py`: move `world_get`, `world_set`, `world_set_body`, and the
   `_world_to_dict` helper from `server.py` here unchanged. Add `register(mcp: FastMCP) -> None`
   that calls `mcp.add_tool(world_get)`, `mcp.add_tool(world_set)`, `mcp.add_tool(world_set_body)`.
2. Create `cac/mcp/prime.py`: move `prime_get`, `prime_applicable_lore`, and the
   `_prime_bundle_to_dict` helper here unchanged. Add `register(mcp: FastMCP) -> None` that calls
   `mcp.add_tool(prime_get)`, `mcp.add_tool(prime_applicable_lore)`.
3. Rewrite `cac/mcp/server.py` to only construct `mcp = FastMCP("cac")`, call `world.register(mcp)`
   and `prime.register(mcp)`, and keep `main()` / the `if __name__ == "__main__"` stdio entry point.
4. Split `tests/mcp/test_server.py`'s existing cases into `tests/mcp/test_world.py` (world tool
   tests) and `tests/mcp/test_prime.py` (prime tool tests), preserving all existing assertions.
   Replace `tests/mcp/test_server.py` with a small composition test asserting
   `{tool.name for tool in mcp.list_tools()}` (or equivalent) contains all five expected tool names.
5. Re-run the existing end-to-end stdio smoke check (spawn the real `cac-mcp` executable via the
   official MCP client, list tools, call one from each domain) to confirm the split didn't change
   externally-visible behavior.

## Verification

- `pdm run pytest -q` passes, with the same tool-behavior coverage as before the split (now spread
  across `test_world.py`/`test_prime.py`) plus the new composition test in `test_server.py`.
- `pdm run ruff check .` and `pdm run ruff format .` are clean, per the `clean-tests-and-lint` world
  lore.
- Manually re-run the stdio smoke test against the rebuilt `cac-mcp` executable: `list_tools` still
  returns all five tools, and calling one tool from each domain (e.g. `world_get` and
  `prime_applicable_lore`) still succeeds with the same shape of response as before the refactor.

## Log

### Review - 2026-07-25T20:41:11Z - John Hoff

Plan reviewed against both applicable lore items. clean-tests-and-lint is satisfied: Verification requires a clean pdm run pytest -q and clean ruff check/ruff format, with no skip/no-verify workarounds proposed. console-best-practices is technically applicable via the region assignment but not materially engaged - the code being restructured (cac/mcp/*) does no rich.Console output, and the lore's own text scopes itself to cac/cli/*, so its absence from the Plan is correctly not a gap. The Plan's description of the current server.py/test_server.py contents and the cac/cli one-module-per-domain precedent it cites both check out against the actual files. One non-lore implementation risk to watch during execution: the register(mcp) -> None / mcp.add_tool(fn) composition mechanism assumes an SDK capability that wasn't verified in this review (out of the cited reading surface) and should be confirmed early rather than assumed - already confirmed by the implementer as a public FastMCP method.

### Message - 2026-07-25T20:44:23Z - John Hoff

Refinement to the composition mechanism (Plan step 1-3): use the SDK's own @mcp.tool() decorator directly in each domain module instead of a bespoke register(mcp) + add_tool() function. The shared FastMCP instance moves to a new cac/mcp/instance.py (mcp = FastMCP("cac")) to avoid a circular import between server.py and the domain modules. world.py and prime.py import mcp from instance.py and decorate their tool functions with @mcp.tool() directly. server.py imports the domain modules (assigned to a _TOOL_MODULES tuple so the import is not flagged as unused by ruff) purely for their @mcp.tool() registration side effects, then exposes main()/mcp.run(). No change to tool names, signatures, or the domain-per-module split itself - only how registration is wired.

### Completed - 2026-07-25T20:54:24Z - John Hoff

Verification passed: pdm run pytest -q (521 passed) and ruff check/format clean. Re-ran the stdio smoke test against the rebuilt cac-mcp.exe: all five tools (world_get, world_set, world_set_body, prime_get, prime_applicable_lore) still list and call correctly, including the error path. Independently confirmed in a resumed Claude Code session connecting to the rebuilt server and calling world_get/prime_applicable_lore successfully. Composition mechanism implemented per the recorded refinement: shared FastMCP instance in cac/mcp/instance.py, @mcp.tool() decorator used directly in world.py/prime.py, server.py reduced to importing the domain modules for their registration side effects plus main().
