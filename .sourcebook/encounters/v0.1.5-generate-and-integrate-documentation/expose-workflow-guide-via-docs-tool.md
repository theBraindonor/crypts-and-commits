---
campaign: v0.1.5-generate-and-integrate-documentation
created_by: John Hoff
created_on: '2026-08-02T16:18:58Z'
depends_on: []
name: expose-workflow-guide-via-docs-tool
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-08-02T16:37:08Z'
---

## Requirements

- A new, read-only "Docs" concept exists: framework-owned reference documents packaged with `cac` (like the skill templates), distinct from `.sourcebook` content — not user-editable data, no create/update/delete operations.
- `docs_list()` MCP tool returns each registered doc's `name` + `summary` (routing signal only, same "summary first" pattern as `lore_list`/`region_list`), cursor-paginated under the response budget for future growth.
- `docs_get(name)` MCP tool returns a named doc's full body, applying `budget_core.truncate_body` — but against a dedicated, larger docs budget constant (not the default 20,000-char `RESPONSE_BUDGET`), since docs are a small, framework-curated set meant to be read whole, not unbounded user-generated content. `workflow.md` (~23.6k chars) must fit under the new budget without truncation.
- `cac docs list` / `cac docs get <name>` CLI commands exist with full MCP parity (`cli-mcp-parity`): same paging contract, same truncation behavior, thin wrappers into `core/docs.py`.
- `workflow.md` (`packages/crypts-and-commits/src/cac/core/templates/docs/workflow.md`) is registered as the first doc, under name `workflow`, with a short routing summary.
- The `world-manager` skill's existing three-step "disclosure ladder" (Orient / Focus a task / Review a plan) gains a fourth step — "Go deeper" — describing when to call `docs_list`/`docs_get` for full procedural/reference detail beyond what lore/region summaries cover. Added to both `templates/skills/claude/world_manager/SKILL.md` and `templates/skills/codex/world_manager/SKILL.md`, matching each flavor's existing tool-name conventions (prefixed `mcp__crypts-and-commits__` in the Claude flavor, bare names in the Codex flavor).
- `workflow.md` documents the new Docs concept itself (tools, CLI fallback, purpose) as required by the `workflow-doc-source-of-truth` lore, since this change adds new MCP tools and touches skill procedure prose.
- `mcp/server.py`'s `_TOOL_MODULES` and `tests/mcp/test_server.py::test_all_domain_tools_are_registered` include the new `docs` module.

## Rationale

The v0.1.5 campaign's goal is to let a project's own `CLAUDE.md`/`AGENTS.md` stay light on CAC internals while still giving an agent access to deep procedural detail when a task actually needs it. The `world-manager` skill already has exactly this shape for lore/region content — a disclosure ladder that goes one tier deeper only as needed. This encounter extends that same ladder one step further, to full guide documents, and proves the mechanism out with the one guide that already exists (`workflow.md`) before any future encounter decides what else belongs in the Docs set or how CLAUDE.md/AGENTS.md guidance itself should be authored.

Mirroring the lore/region `list` (summaries) + `get` (full body) pattern keeps this consistent with the rest of the domain model instead of inventing a new shape, and keeps the door open for more docs to be registered later without a redesign.

## Plan

1. Add `DOCS_RESPONSE_BUDGET` to `core/config.py` (a larger character ceiling than `RESPONSE_BUDGET`, sized comfortably above `workflow.md`'s current length).
2. Add `core/docs.py`: a private static registry mapping doc name -> (template package/filename, summary); `list_docs()` (name+summary pairs), `read_doc(name)` (raises a `DocNotFoundError` for unknown names, otherwise loads via `cac.core.templates.load`), and a helper resolving the packaged file's real filesystem path (for the truncation fallback notice). Register `workflow` -> `templates/docs/workflow.md` with a one-line summary.
3. Add `mcp/docs.py`: `docs_list(cursor)` (paginated via `budget_core.paginate`) and `docs_get(name)` (body truncated via `budget_core.truncate_body` with `DOCS_RESPONSE_BUDGET`). Wire into `mcp/server.py`'s `_TOOL_MODULES`.
4. Add `cli/docs.py`: `cac docs list` / `cac docs get <name>` Typer commands mirroring `cli/region.py`'s structure (rich console output, `markup=False` for stored/doc body content per `console-best-practices`, `fail()` on unknown name). Register in `cli/app.py`.
5. Update `templates/skills/claude/world_manager/SKILL.md` and `templates/skills/codex/world_manager/SKILL.md`: add a "Docs" section (mirroring the existing "Prime" section) describing `docs_list`/`docs_get` + CLI fallback, and append step 4 ("Go deeper") to the disclosure ladder.
6. Update `templates/docs/workflow.md`: extend "Cross-cutting: priming and search" (retitled to include docs) with a short "Docs" bullet describing the new tools/CLI commands and their purpose; note in the "This document" section that the guide itself is now retrievable via `docs_get("workflow")`.
7. Add/extend tests: `tests/core/test_docs.py`, `tests/mcp/test_docs.py`, `tests/cli/test_docs.py`, and the registration list in `tests/mcp/test_server.py::test_all_domain_tools_are_registered`.
8. Run `pdm run pytest -q` and `pdm run ruff check .` / `pdm run ruff format .`, fixing anything that fails.

## Verification

- `pdm run pytest -q` passes in full (no skips or deletions to dodge failures).
- `pdm run ruff check .` reports zero errors; `pdm run ruff format .` reports no diffs.
- Manually run `pdm run cac docs list` (shows `workflow`) and `pdm run cac docs get workflow` (prints the full, untruncated guide) to confirm CLI behavior end to end.
- Confirm `workflow.md`'s own body was updated to describe the new Docs concept, and that both `world_manager/SKILL.md` flavors carry the new ladder step, before asking the user to confirm completion.

## Log

### Review - 2026-08-02T16:24:21Z - John Hoff

The Plan is sound and consistent with clean-tests-and-lint, cli-mcp-parity, console-best-practices, and workflow-doc-source-of-truth — MCP/CLI parity, paging/truncation, markup handling, and the workflow.md update are all explicitly planned and verified against the actual current file structure. One gap against skills-authored-only-in-templates: the Plan correctly edits the template paths for both SKILL.md flavors but never adds a step asking the developer to run `cac bootstrap init` to deploy the change, as that lore's review checklist explicitly requires — recommend adding this to the Plan or Verification before/while executing, even though it's a minor, easily-added step rather than a structural conflict.

### Message - 2026-08-02T16:26:04Z - John Hoff

Additional verification, per the review note: this repo's own .claude/skills/ and .agents/skills/ world-manager copies are deployed artifacts, not the templates edited by this Plan's step 5. The new "Go deeper" disclosure-ladder step is not actually live here until the developer runs `cac bootstrap init` to redeploy from the updated templates. Before asking the user to confirm completion, confirm with them whether that redeploy has been (or will be) run — do not attempt to run `cac bootstrap init` unilaterally, per the developer-only guardrail.

### Completed - 2026-08-02T16:37:08Z - John Hoff

Docs concept implemented end to end: core/docs.py registry, mcp/docs.py + cli/docs.py with full parity, workflow.md registered and served untruncated under DOCS_RESPONSE_BUDGET, world-manager SKILL.md (both flavors) gained a fourth disclosure-ladder step, and workflow.md documents the new Docs cross-cutting capability. Full pytest suite (708+15 tests) and ruff clean. Redeployed via cac bootstrap init and verified live: docs_list/docs_get work over MCP, and both .claude/skills and .agents/skills world-manager copies carry the new section/step.
