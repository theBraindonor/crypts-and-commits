---
campaign: v0.1.0-bootstrapping
created_by: John Hoff
created_on: '2026-07-25T01:22:33Z'
name: 07-depends-on-frontmatter-field
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-07-25T03:49:47Z'
---

# Depends-On Frontmatter Field

## Requirements

- Add a `depends_on` field to encounter frontmatter. It stores the names of direct prerequisite encounters within the same campaign. Existing encounters without the field remain valid and behave as though `depends_on: []` were present.
- Add `cac encounter assign-dependency <encounter> <prerequisite>` and `cac encounter unassign-dependency <encounter> <prerequisite>`. Dependency mutation is permitted only while the dependent encounter is `draft` or `reviewed`, and assignment/unassignment is idempotent.
- Reject dependency assignment when the prerequisite does not exist in the campaign, is the dependent encounter itself, is already `abandoned`, or would create a direct or transitive cycle.
- Preserve an existing dependency if its prerequisite is later abandoned. The abandoned prerequisite remains visible as an unsatisfied blocker until the dependency is removed or replaced.
- Prevent an encounter from moving from `reviewed` to `open` unless every direct dependency is `completed`. Report all unsatisfied direct dependencies and their statuses in one actionable error.
- Reject deletion of an encounter while any other encounter in the campaign depends on it; report the dependent encounter names rather than leaving dangling references.
- Add `cac encounter order [--campaign <campaign>]` without changing the existing oldest-updated behavior of `cac encounter list`. The new command must include all campaign encounters, including completed and abandoned entries, in deterministic topological order.
- For encounters not ordered relative to one another by dependencies, order by `created_on` and then encounter name. Do not use `updated_on`, because routine metadata changes must not reshuffle execution order.
- Print one encounter per line from `encounter order`, including its status and direct dependencies, for example `api [draft] depends_on: foundation`; use `(none)` when there are no dependencies.
- If stored legacy or externally corrupted data contains a missing dependency or cycle, `encounter order` must fail with a diagnostic identifying the missing reference or the encounters participating in the cycle.

## Rationale

This campaign used numeric encounter-name prefixes to imply creation and execution order. That convention is neither authoritative nor inspectable as a graph, and it cannot enforce prerequisite completion. A first-class `depends_on` field makes direct relationships part of each encounter, supports deterministic planning views, and integrates ordering with the encounter lifecycle. Keeping `encounter list` unchanged preserves its existing inventory semantics, while a dedicated `encounter order` command provides the graph-oriented view. Allowing edits through `reviewed` keeps an encounter recoverable when a prerequisite is abandoned, while locking dependency changes once work opens prevents the approved execution graph from changing underneath active or finished work.

## Plan

1. Update `packages/crypts-and-commits/src/cac/core/templates/sourcebook/encounter.md` and the `Encounter` model in `packages/crypts-and-commits/src/cac/core/encounter.py` to include `depends_on`, defaulting missing metadata to an empty list for backward compatibility.
2. Implement dependency-domain operations and focused exceptions in `packages/crypts-and-commits/src/cac/core/encounter.py`: idempotent assignment/unassignment with dependent-status gating; same-campaign existence, self-reference, abandoned-target, and cycle validation; reverse-reference checks for deletion; deterministic topological ordering with created-time/name tie-breaking; and diagnostics for invalid stored graphs.
3. Integrate dependencies with lifecycle transitions in `packages/crypts-and-commits/src/cac/core/encounter.py` so opening reports every direct prerequisite not in `completed` status. Preserve abandoned references as blockers that can still be removed while the dependent is `reviewed`.
4. Add thin Typer wrappers in `packages/crypts-and-commits/src/cac/cli/encounter.py` for `assign-dependency`, `unassign-dependency`, and `order`; translate core errors into actionable CLI failures; and render the order output as CLI-authored status/dependency lines without changing `encounter list`.
5. Extend `packages/crypts-and-commits/tests/core/test_encounter.py` for schema defaults, mutation lifecycle rules, idempotency, validation, cycle detection, deletion protection, opening gates, invalid stored graphs, stable tie-breaking, and topological ordering. Extend `packages/crypts-and-commits/tests/cli/test_encounter.py` for the three command surfaces, output, campaign resolution, and error propagation. Update template/bootstrap assertions where the new default frontmatter field affects them.
6. Update both `.agents/skills/campaign-manager/SKILL.md` and `.claude/skills/campaign-manager/SKILL.md` with the dependency commands, ordering view, mutation constraints, deletion rule, and opening prerequisite gate. Update the encounter domain description in `CLAUDE.md` if needed so repository-level guidance reflects the new field and lifecycle behavior.

## Verification

- Run focused core tests: `pdm run pytest packages/crypts-and-commits/tests/core/test_encounter.py -q`.
- Run focused CLI tests: `pdm run pytest packages/crypts-and-commits/tests/cli/test_encounter.py -q`.
- Confirm a legacy encounter without `depends_on` reads as an empty dependency list, while newly created encounters persist `depends_on: []`.
- Confirm assignment and unassignment are idempotent in `draft` and `reviewed`, and rejected for `open`, `completed`, and `abandoned` dependents.
- Confirm missing, self, abandoned, and cycle-forming assignments fail without modifying the encounter.
- Confirm opening reports all non-completed direct prerequisites with statuses, and succeeds once all are completed.
- Confirm deletion reports all dependent encounters and leaves the referenced encounter intact.
- Confirm `encounter order` includes every encounter, places prerequisites before dependents, uses `created_on` then name for unrelated nodes, remains stable after `updated_on` changes, displays statuses and direct dependencies, and diagnoses missing references and cycles in invalid stored data.
- Confirm the existing `encounter list` ordering and pagination behavior remain unchanged.
- Run the complete required quality gates: `pdm run pytest -q`, `pdm run ruff check .`, `pdm run ruff format .`, and `pdm run ruff format . --check`. Fix all failures without skips, weakened tests, suppression bypasses, or `--no-verify`.

## Log

### Review - 2026-07-25T03:40:08Z - John Hoff

The plan honors both applicable lore entries: it retains domain logic in core with thin Typer wrappers, treats the new order display as CLI-authored status/frontmatter-style output consistent with the console-printing convention, and requires the complete pytest and Ruff quality gates with formatting fixes and no skips, weakened tests, suppression bypasses, or --no-verify. PASS-WITH-NOTES: the template/bootstrap assertion files are not named, so that affected surface is not independently inspectable within the review boundary; implementation must also continue using markup=False for any stored or free-form content if the eventual output expands beyond CLI-authored metadata lines.

### Opened - 2026-07-25T03:40:54Z - John Hoff

User approved implementation after independent review.

### Message - 2026-07-25T03:48:52Z - John Hoff

Implementation completed. Added backward-compatible depends_on metadata, dependency mutation commands and validation, lifecycle opening/deletion gates, deterministic encounter order output, focused core/CLI coverage, and updated both campaign-manager skill copies plus CLAUDE.md. Verification passed on the final formatted state: core encounter tests 84 passed; CLI encounter tests 55 passed; full suite 486 passed; ruff check clean; ruff format check confirmed 51 files formatted; git diff --check clean.

### Completed - 2026-07-25T03:49:47Z - John Hoff

User confirmed completion after all verification gates passed: 486 tests, Ruff lint clean, formatting check clean, and Git whitespace check clean.
