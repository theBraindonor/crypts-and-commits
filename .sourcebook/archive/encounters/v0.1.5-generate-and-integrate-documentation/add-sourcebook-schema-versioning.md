---
archived: true
campaign: v0.1.5-generate-and-integrate-documentation
created_by: John Hoff
created_on: '2026-08-02T17:05:49Z'
depends_on: []
name: add-sourcebook-schema-versioning
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-08-02T22:47:30Z'
---

## Requirements

- `core/config.py` gains `SOURCEBOOK_SCHEMA_VERSION = 1` and `SCHEMA_VERSION_KEY = "schema_version"`. The current, pre-versioning sourcebook format is retroactively defined as version 1, so nothing that exists today is flagged as needing migration.
- `world_core.initialize_world()` stamps `schema_version` onto a brand-new `world.md` at creation time (auto-populated on first `cac bootstrap init`).
- A new read-only `world_core` function (e.g. `check_schema_version(root)`) reads an *existing* world file's `schema_version` (missing attribute implies version 1, for sourcebooks bootstrapped before this feature existed), compares it against `SOURCEBOOK_SCHEMA_VERSION`, and reports one of `current` / `behind` / `ahead`. It never mutates the file.
- `cac bootstrap init` calls this check whenever `world.md` already existed (not on fresh creation) and reports the result: quiet/no extra message on `current`; on `behind`, a clear message telling the developer to have their coding assistant run the migration via the `world-manager` skill; on `ahead` (sourcebook newer than the installed `cac`), a clear message telling the developer to upgrade their installed `cac` package. Bootstrap only reports - it never writes `schema_version` for a pre-existing file; only a completed migration does that.
- A new `migration-guide` doc is registered in `core/docs.py` (reusing the existing `docs_get`/`docs_list` MCP/CLI surface from the `expose-workflow-guide-via-docs-tool` encounter - no new tool needed), backed by a new `templates/docs/migration-guide.md`.
- `migration-guide.md` states the current schema version at the top, and - regardless of there being no version-to-version transition to document yet - includes a **generic, version-independent procedure** covering the fact that a real migration is very likely to need direct edits to `.sourcebook/` files, breaking the project's normal MCP/CLI-only guardrail: the existing generic per-object setters (`world_set`, `lore_set_summary`, etc.) can't perform arbitrary structural changes a schema change may require (e.g. renaming a frontmatter key across every file of a type, restructuring body sections). This procedure must cover, at minimum:
  1. Get the developer's explicit, informed approval before disabling any guardrail mechanism - a bigger ask than a normal encounter approval, since it's turning off a project safety mechanism, not just approving a plan.
  2. Record which guardrail mechanism(s) are active for the current session (Claude Code's `Edit(.sourcebook/**)` deny rule in `.claude/settings.json`; Codex's `PreToolUse` sourcebook-guard hook registration in `.codex/config.toml`) before touching anything, so they can be restored to their exact prior state.
  3. Temporarily remove/disable the applicable guardrail mechanism(s).
  4. Perform the migration's direct file edits.
  5. Restore the guardrail mechanism(s) to their exact prior state immediately afterward - unconditionally, even if the migration is aborted or fails partway through.
  6. Only after the guardrail is restored, verify the migrated content through normal MCP/CLI calls (e.g. `world_get`, `lore_list`/`lore_get`, `region_list`/`region_get`) and set the new `schema_version` via `world_set`.
  7. Confirm with the developer that the guardrail was restored and the migration verified, before considering the work done.
  The doc also documents the format for future `## Migrating from version N to N+1` sections (none exist yet at version 1), so maintainers have a consistent pattern to follow the next time `SOURCEBOOK_SCHEMA_VERSION` bumps.
- `world-manager`'s `SKILL.md` (both Claude and Codex flavors) gains a new section: check `schema_version` (from `world_get()`/`prime_get()`) against the version stated at the top of `docs_get("migration-guide")`; when behind, consult that doc, follow its generic guardrail-suspend/restore procedure together with any applicable version-specific sections, then call `world_set("schema_version", ...)` once complete.
- `docs/workflow.md` is updated per `workflow-doc-source-of-truth`: document the new `schema_version` world attribute and the `migration-guide` doc + its procedure, since this changes skill procedure and adds new domain-level structure.
- Tests extended: `tests/core/test_world.py` (stamping on creation; `check_schema_version` outcomes including the missing-attribute-implies-1 case), `tests/core/test_bootstrap.py` / `tests/cli/test_bootstrap.py` (console messages for behind/ahead/current), `tests/core/test_docs.py` / `tests/mcp/test_docs.py` / `tests/cli/test_docs.py` (new `migration-guide` entry registered, content readable).

## Rationale

Sourcebook schema changes are inevitable as the domain model evolves, but a hand-maintained migration *tool* would be complex, rarely exercised, and far less adaptable than simply having the agent read a guide and make the changes itself - the same "have the agent do the work" philosophy already underlying this framework. This encounter lays that foundation: the version field, the bootstrap-time detection, and the doc the agent consults, mirroring the disclosure-ladder "docs" mechanism the previous encounter (`expose-workflow-guide-via-docs-tool`) already built, rather than inventing a new one.

The guardrail-suspension procedure is captured now, before any real migration exists to force the issue, specifically because it's easy to forget under the pressure of an actual future migration: getting it wrong either blocks the agent from making changes a migration genuinely requires, or - worse - leaves the project permanently unguarded if restoration is skipped. Writing the generic procedure into the doc now, while it's uncontroversial and low-stakes, means the first real migration inherits a documented, deliberate answer instead of an improvised one.

## Plan

1. Add `SOURCEBOOK_SCHEMA_VERSION` and `SCHEMA_VERSION_KEY` to `core/config.py`.
2. In `core/world.py`: set `post[SCHEMA_VERSION_KEY] = SOURCEBOOK_SCHEMA_VERSION` in `initialize_world()` when the file is newly created; add `check_schema_version(root)` returning the stored (or implied) version, the current constant, and a `current`/`behind`/`ahead` outcome, without writing anything.
3. In `cli/bootstrap.py`'s `init` command: when `world_created` is `False`, call `check_schema_version` and print the appropriate message for each outcome (styled consistently with the existing `_report_*` helpers).
4. Add `templates/docs/migration-guide.md` with: the current schema version stated at the top, the generic guardrail-suspend/restore procedure (Requirements list above) written out in full, and the documented format for future version-specific sections.
5. Register `migration-guide` in `core/docs.py`'s `_DOCS` map with a short routing summary.
6. Update `templates/skills/claude/world_manager/SKILL.md` and `templates/skills/codex/world_manager/SKILL.md`: add the new schema-version-check section described above, matching each flavor's existing tool-name conventions.
7. Update `templates/docs/workflow.md`: document the `schema_version` world attribute and the `migration-guide` doc/procedure.
8. Add/extend tests per the Requirements list.
9. Run `pdm run pytest -q` and `pdm run ruff check .` / `pdm run ruff format .`, fixing anything that fails.

## Verification

- `pdm run pytest -q` passes in full (no skips or deletions to dodge failures).
- `pdm run ruff check .` reports zero errors; `pdm run ruff format .` reports no diffs.
- Manually run `cac bootstrap init` against a fresh scratch directory to confirm a new `world.md` carries `schema_version: 1`; manually edit a scratch copy's `world.md` to remove/lower the attribute and re-run `cac bootstrap init` to confirm the `behind` message appears; confirm `pdm run cac docs get migration-guide` prints the full guide including the guardrail procedure.
- Confirm both `world_manager/SKILL.md` flavors and `docs/workflow.md` carry the new content before asking the user to confirm completion.
- Before completion, confirm with the developer whether `cac bootstrap init` will be re-run in this repo to redeploy the updated skill templates and backfill this repo's own `.sourcebook/world.md` with `schema_version` - same precedent as `expose-workflow-guide-via-docs-tool` - since the deployed `.claude/skills`/`.agents/skills` copies are not source and won't reflect this change until redeployed.

## Log

### Review - 2026-08-02T17:09:03Z - John Hoff

Reviewed against all five applicable lore items (clean-tests-and-lint, cli-mcp-parity, console-best-practices, skills-authored-only-in-templates, workflow-doc-source-of-truth) — the Plan honors each: full pytest/ruff gate is in Verification, no new CLI surface is added so no MCP-parity gap arises (the new migration-guide doc deliberately reuses the existing docs_get/docs_list tools), bootstrap's new console messages are CLI-authored text outside the markup=False rule, skill changes correctly target the templates/skills paths with developer-only redeployment called out in Verification, and workflow.md is explicitly scheduled for update in the same change. Two non-blocking notes for the GM: depends_on is empty despite the Plan building on expose-workflow-guide-via-docs-tool's docs surface — worth confirming that encounter is actually completed before opening this one; and check_schema_version is deliberately not exposed as its own tool (SKILL.md compares world_get()/prime_get() output by hand instead) — worth a quick confirmation that's intentional rather than an oversight.

### Completed - 2026-08-02T17:28:55Z - John Hoff

Sourcebook schema versioning implemented end to end: SOURCEBOOK_SCHEMA_VERSION/schema_version stamped on fresh world.md, read-only check_schema_version reporting behind/ahead/current from cac bootstrap init, and a new migration-guide doc (registered via the existing docs_get/docs_list surface) documenting both the generic guardrail-suspend/restore procedure a real migration will need and the format for future version-specific sections. Both world-manager SKILL.md flavors and workflow.md updated to match. Full pytest suite (722 tests) and ruff clean; manually verified fresh-stamp, behind-warning, ahead-warning, and migration-guide content. Redeployed via cac bootstrap init and this repo's own world.md backfilled to schema_version 1.
