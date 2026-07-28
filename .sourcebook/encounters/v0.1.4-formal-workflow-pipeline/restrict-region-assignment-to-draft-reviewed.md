---
campaign: v0.1.4-formal-workflow-pipeline
created_by: John Hoff
created_on: '2026-07-28T03:32:12Z'
depends_on: []
name: restrict-region-assignment-to-draft-reviewed
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-07-28T04:30:18Z'
---

## Requirements

- Mirror the existing dependency-mutation restriction in `packages/crypts-and-commits/src/cac/core/encounter.py` (`_DEPENDENCY_MUTATION_STATUSES = frozenset({"draft", "reviewed"})`, enforced via `_require_dependency_mutable` for `assign_dependency`/`unassign_dependency`) onto region assignment: `assign_region`/`unassign_region` must only be permitted while an encounter's status is `draft` or `reviewed`.
- Attempting to assign or unassign a region outside `draft`/`reviewed` must raise a clear, typed error - a new exception distinct from `EncounterDependencyMutationError` (e.g. `EncounterRegionMutationError`), since region assignment and dependency assignment are separate concerns that happen to share this restriction shape, not the same concern.
- Propagate the new restriction and its error through both interaction surfaces: the MCP tools `encounter_assign_region`/`encounter_unassign_region` (`mcp/encounter.py`) and the CLI commands `cac encounter assign-region`/`unassign-region` (`cli/encounter.py`) - the CLI command should catch and report the new error the same way it already catches `EncounterDependencyError` subclasses for the dependency commands.
- Scope is limited to encounter-to-region assignment only. No change to lore's region/world assignment (`lore_assign_region`/`lore_assign_world` etc.) - those target objects (lore, region, world) have no status lifecycle at all, so there is nothing analogous to mirror there.
- Once implemented, update this campaign's `author-workflow-reference-guide` deliverable (`packages/crypts-and-commits/src/cac/core/templates/docs/workflow.md`) to drop the now-inaccurate "region assignment carries no status restriction" note and describe the new, matching restriction instead.

## Rationale

While verifying the workflow reference guide (the prior encounter in this campaign), we confirmed that encounter region assignment currently has **no** status restriction at all, in contrast to dependency assignment, which is already restricted to `draft`/`reviewed`. That asymmetry is a plausible contributor to this campaign's stated gap that region assignment "is frequently skipped when creating/reviewing encounters": because nothing closes off the ability to assign a region at any point in an encounter's life, there's no structural pressure to get it right during planning/review the way dependency assignment already has - it's always deferrable, so it's easy to defer indefinitely.

This change doesn't by itself guarantee a region gets assigned (that's a discipline/skill-level concern, not purely a code-level one), but it removes the inconsistency and closes the "I'll add it later" workaround: once an encounter passes `reviewed` into `open`, its region assignment - like its dependency graph - is settled. That gives the independent reviewer subagent (per the `campaign-manager` skill's draft -> reviewed gate) a real, enforceable checkpoint to flag a missing or wrong region assignment before it becomes permanent for that encounter's `open`/`completed` lifetime.

## Plan

1. **`core/encounter.py`**
   - Add `_REGION_MUTATION_STATUSES = frozenset({"draft", "reviewed"})`, next to `_DEPENDENCY_MUTATION_STATUSES`.
   - Add `class EncounterRegionMutationError(ValueError)`, defined alongside the other encounter exceptions (not a subclass of `EncounterDependencyError` - a separate concern, per Requirements).
   - Add a `_require_region_mutable(post, name)` helper mirroring `_require_dependency_mutable`, raising `EncounterRegionMutationError` with a message in the same shape ("Cannot change regions for encounter %r: status is %r, but region changes require status to be one of: %s.").
   - Call `_require_region_mutable` from `_update_regions` (the shared helper backing both `assign_region` and `unassign_region`), before `toggle_list_attribute` runs, so both directions are covered by one call site. `assign_region`'s existing `region_core.exists` check stays as-is, ahead of the mutability check or after - existing tests for missing-region should keep passing regardless of ordering, but the mutability check will run for `unassign_region` too since it has no equivalent existence check today.

2. **`mcp/encounter.py`**
   - No signature changes needed. `encounter_assign_region`/`encounter_unassign_region` already just call into `core`, so the new error propagates automatically through FastMCP's exception handling, the same as `EncounterDependencyMutationError` does today for the dependency tools.

3. **`cli/encounter.py`**
   - In `assign_region` and `unassign_region`, add `encounter_core.EncounterRegionMutationError` to the caught exception tuple (alongside the existing `EncounterNotFoundError`/`RegionNotFoundError`/`GitIdentityError`), so `fail(console, str(exc))` reports it the same way the dependency commands already report `EncounterDependencyError`.

4. **Tests** (mirroring the existing dependency-mutation test shape in each layer):
   - `tests/core/test_encounter.py`: a parametrized test analogous to `test_dependency_changes_are_rejected_after_reviewed` - for `terminal_status` in `["open", "completed", "abandoned"]`, assert `assign_region`/`unassign_region` both raise `EncounterRegionMutationError`. A companion test analogous to `test_dependency_changes_are_allowed_while_reviewed` confirming both still work while `reviewed`.
   - `tests/mcp/test_encounter.py`: one test confirming `encounter_assign_region` (or `unassign_region`) raises once the encounter is `open`.
   - `tests/cli/test_encounter.py`: one test confirming `cac encounter assign-region` on an `open` encounter exits non-zero via `fail`.

5. **`templates/docs/workflow.md`**
   - Replace lines 76-79 ("Unlike the encounter's `depends_on` list, region assignment carries **no status restriction** - it can be changed regardless of the encounter's current status.") to instead state that, like `depends_on`, region assignment is one-directional with no back-reference, and is now also restricted to `draft`/`reviewed`.
   - Replace the standalone sentence "Region assignment/unassignment carries no status restriction. Dependency assignment/unassignment is only permitted while `draft` or `reviewed`." (near the encounter status-flow diagram) with a single sentence stating both region and dependency assignment/unassignment are only permitted while `draft` or `reviewed`.

6. Run `pdm run ruff format .` and `pdm run ruff check .` as part of implementation, not just at the end, per the `clean-tests-and-lint` world lore.

## Verification

- `pdm run pytest -q` passes in full, including the new core/mcp/cli tests described above, with no skips or deletions to dodge failures.
- `pdm run ruff check .` reports zero errors; `pdm run ruff format .` reports no diffs.
- Manually confirm the fix with `pdm run cac`: create a throwaway campaign/encounter, review it, open it, then attempt `cac encounter assign-region <name> <region> -c <campaign>` and confirm it fails with the new `EncounterRegionMutationError` message rather than silently succeeding.
- Read the updated `packages/crypts-and-commits/src/cac/core/templates/docs/workflow.md` sections by eye to confirm the "no status restriction" language is gone and replaced with an accurate description matching the new code behavior.

## Log

### Review - 2026-07-28T04:10:06Z - John Hoff

Reviewed against all five applicable lore items (clean-tests-and-lint, cli-mcp-parity, console-best-practices, skills-authored-only-in-templates, workflow-doc-source-of-truth) and passes. The Plan mirrors the existing `_DEPENDENCY_MUTATION_STATUSES`/`_require_dependency_mutable` pattern faithfully via a shared `_update_regions` call site, correctly identifies that no MCP signature change is needed (verified: the MCP tools already call straight into `core`), correctly adds the new `EncounterRegionMutationError` to `cli/encounter.py`'s existing catch tuples, budgets ruff/pytest checks throughout rather than only at the end (clean-tests-and-lint), and updates both stale "no status restriction" passages in `templates/docs/workflow.md` (verified present at lines 76-79 and 269-270) in the same change (workflow-doc-source-of-truth). No lore conflicts found; no unverifiable concerns to flag.

### Message - 2026-07-28T04:23:10Z - John Hoff

Verification deviation: the Plan's third bullet called for a manual `pdm run cac` walkthrough in a throwaway campaign/encounter, but that requires `cac bootstrap init` first, which CLAUDE.md forbids the assistant from ever running, even to fix a missing `.sourcebook`. User agreed the automated `tests/cli/test_encounter.py::test_assign_region_rejected_once_open` test satisfies this bullet instead, since it drives the identical `cac encounter assign-region` CLI path via CliRunner against an open encounter and asserts exit_code == 1.

### Completed - 2026-07-28T04:30:18Z - John Hoff

Implemented, tested (689 passed, ruff clean), and workflow.md updated. Manual pdm run cac walkthrough swapped for the automated CLI test per logged deviation.
