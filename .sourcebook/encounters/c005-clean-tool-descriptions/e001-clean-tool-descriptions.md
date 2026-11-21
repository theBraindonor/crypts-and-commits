---
archived: false
campaign: c005-clean-tool-descriptions
created_by: John Hoff
created_on: '2026-11-21T15:51:53Z'
depends_on: []
kind: scripted
name: e001-clean-tool-descriptions
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-11-21T16:04:19Z'
---

## Requirements

Vanquish b007-clean-reference-tool-descriptions as scoped by the developer while drafting (rulings c005-e001-clean-all-mcp-descriptions-centrally and c005-e001-tailor-contract-footer-per-domain):

1. Every MCP tool description and every `cac` command's help text has no stray interior whitespace: no run of two or more spaces after non-space text, and no newline followed by indentation.
2. Reference-decorated tools and commands: `references.inputs` (`packages/crypts-and-commits/src/cac/core/references.py`, around line 306) cleans the wrapped function's docstring with `inspect.cleandoc` before appending the identity-contract footer.
3. Undecorated MCP tools: descriptions are cleaned centrally at registration in `packages/crypts-and-commits/src/cac/mcp/instance.py`, without editing the individual tool modules.
4. The contract footer is tailored per domain: the sentence "Qualified encounter context overrides active fallback and must agree with an explicit campaign." appears only on encounter-domain tools and commands (`references.inputs("encounter", ...)`, including `prime_applicable_lore` / `cac prime applicable-lore`), not on boss, campaign or rumor ones. The ruling footer and every other footer sentence stay unchanged.
5. `packages/crypts-and-commits/src/cac/core/templates/docs/tool-reference.md` (Short references section) documents the domain-specific footer, per `workflow-doc-source-of-truth`.
6. No behavior or signature change to any tool or command.

Measured before the change, on c005 at 192871f: 38 of 85 MCP tool descriptions and 11 of 87 CLI commands' raw help contain indentation runs. 24 of the MCP cases are reference-decorated; the other 14 (`docs_*`, `index_*`, `world_*`, `lore_*`, `region_*`, `prime_get`) are undecorated, because `MCPServer` (mcp 2.3.0) does not clean docstrings. Typer already cleans undecorated CLI docstrings, so all 11 CLI cases are decorated.

## Rationale

Agents read these descriptions on every tool call, and developers read `cac ... --help`. c004 made the content accurate; this makes it render cleanly (e.g. `cac campaign complete --help` currently shows "...open encounter.     The required message..."). The root cause is that `(function.__doc__ or "") + contract` puts an unindented line after indented continuation lines, so docstring cleaning keeps the indentation. Undecorated MCP tools leak for a different reason: the SDK passes raw docstrings through. A repository-wide guard keeps both cases from coming back. The encounter-context sentence is misleading on boss, campaign and rumor tools, which take no encounter reference.

## Plan

1. `core/references.py` `inputs.decorate`: build the docstring as `inspect.cleandoc(function.__doc__ or "")`, then the footer on a new line. Build the non-ruling footer from its existing sentences, adding the "Qualified encounter context..." sentence only when `domain == "encounter"`. The ruling footer text is unchanged.
2. `mcp/instance.py`: replace the bare `MCPServer(...)` with a thin subclass whose `tool()` returns a decorator that, when no explicit `description` is passed, registers the function with `description=inspect.cleandoc(fn.__doc__)` (None when absent). Every other argument passes through unchanged. `mcp` stays the module-level instance, so tool modules and `server.py` are untouched.
3. Guard tests, mirroring existing test modules:
   - `tests/mcp/` (server/instance test module): list every registered tool via `mcp.list_tools()` after importing `cac.mcp.server`, assert the count is nonzero, and assert that no description matches `\S {2,}` or `\n[ \t]+`.
   - `tests/cli/test_app.py`: walk the Typer app's click command tree (`typer.main.get_command`, recursing on anything with `.commands`), and assert the same patterns are absent from every leaf command's `help`. A comment notes that undecorated CLI help relies on Typer/click's own docstring cleaning, which the walk verifies.
   - `tests/core/test_references.py`: the encounter-domain footer contains the qualified-context sentence; boss, campaign and rumor footers do not; the ruling footer is unchanged.
4. `tool-reference.md` Short references section: one sentence saying the appended reference-contract text mentions qualified encounter context only on encounter tools and commands.
5. Spot-check `cac campaign complete`, `cac campaign set-bosses`, `cac campaign delete`, `cac encounter assign-region` and `cac encounter open` with `--help`, plus a few MCP descriptions (`world_get`, `campaign_complete`, `encounter_open`).

## Verification

- The new guard tests fail on the pre-change code (confirmed before applying steps 1-2) and pass afterwards.
- Re-running the measurement reports 0 of 85 MCP descriptions and 0 of 87 CLI commands with indentation runs.
- The spot-checked help and descriptions read as clean prose; boss/rumor/campaign footers lack the encounter sentence, encounter ones keep it.
- Per `clean-tests-and-lint`: `pdm run pytest -q` passes, `pdm run ruff check .` reports zero errors, and `pdm run ruff format .` produces no diffs.

## Log

### Review - 2026-11-21T15:54:14Z - John Hoff

Independent review PASS-WITH-NOTES against clean-tests-and-lint, cli-mcp-parity, console-best-practices, skills-authored-only-in-templates and workflow-doc-source-of-truth. The Plan fixes the whitespace leaks at their two verified root causes (references.inputs concatenating the footer onto an uncleaned docstring at references.py:306, and MCPServer passing raw docstrings for undecorated tools, fixed centrally through a tool() subclass in mcp/instance.py, whose description= keyword was confirmed in mcp 2.3.0). Because the footer is shared, MCP and CLI descriptions keep agreeing. The new domain-specific footer fact is documented in tool-reference.md's Short references section next to the existing ruling-footer note, as workflow-doc-source-of-truth requires. No procedure change means the phase guides correctly stay untouched. Guard tests check whitespace patterns rather than prose wording and must fail before the fix, and Verification includes the pytest/ruff gate. No console or skill-template surface is touched. Notes: name the MCP guard's test module explicitly (tests/mcp/test_server.py); confirm during implementation that every tool accepting a qualified cNNN/eNNN reference is decorated with the encounter domain, so the tailored footer stays accurate; keep cleandoc idempotent and None-safe for missing docstrings; fix any deliberate double space the guard flags rather than loosening the regex.

### Message - 2026-11-21T16:03:10Z - John Hoff

Implemented per Plan. Reviewer notes addressed: MCP guard lives in tests/mcp/test_server.py; only encounter-domain selection parses qualified cNNN/eNNN context (all 15 encounter tools/commands plus prime applicable-lore use domain "encounter"; campaign tools take no encounter refs), so the tailored footer is accurate; instance.py's CleanDescriptionServer passes None for missing docstrings and cleandoc is idempotent on already-clean ones (decorated tools); no deliberate double spaces were flagged. Guard tests failed pre-fix (8 failures) and pass after. Re-measurement: 0/85 MCP descriptions, 0/87 CLI commands with indentation runs. Spot-checked help for campaign complete/set-bosses/delete, encounter assign-region/open, and MCP world_get/campaign_complete/encounter_open/boss_get/rumor_get/prime_applicable_lore/ruling_get. pdm run pytest -q: 1735 passed; ruff check clean; ruff format reformatted one new test file, then 341 files already formatted.

### Completed - 2026-11-21T16:04:19Z - John Hoff

Verification passed and confirmed by the developer: guards failed pre-fix and pass after; 0/85 MCP and 0/87 CLI descriptions with indentation runs; pytest 1735 passed; ruff check and format clean.
