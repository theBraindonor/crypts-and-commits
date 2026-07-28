---
campaign: v0.1.4-formal-workflow-pipeline
created_by: John Hoff
created_on: '2026-07-28T04:41:59Z'
depends_on: []
name: require-region-before-review
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-07-28T05:02:17Z'
---

## Requirements

- `encounter_review` (the `draft` -> `reviewed` transition) must fail unless the encounter already has at least one region assigned. Raise a new, distinct, typed error - e.g. `EncounterRegionRequiredError` (not `EncounterRegionMutationError`, which is about the *mutation window*, a separate concern) - when a `draft` encounter with an empty `regions` list is reviewed.
- Tighten both `_REGION_MUTATION_STATUSES` and `_DEPENDENCY_MUTATION_STATUSES` in `packages/crypts-and-commits/src/cac/core/encounter.py` from `frozenset({"draft", "reviewed"})` down to `frozenset({"draft"})`. Once an encounter is `reviewed`, neither its `regions` list nor its `depends_on` list may change anymore - matching how the four fixed body sections already lock at `reviewed`. No new error types are needed for this part; `EncounterRegionMutationError`/`EncounterDependencyMutationError` already exist and their messages are derived from the frozensets, so narrowing the sets alone changes the enforced window and the generated message text.
- Propagate the new `EncounterRegionRequiredError` through both interaction surfaces: `mcp/encounter.py`'s `encounter_review` needs no code change (errors already propagate automatically, per `cli-mcp-parity`), but `cli/encounter.py`'s `review` command must add it to its caught-exception tuple so it reports via `fail()` instead of an unhandled traceback.
- Update every docstring/help string that currently says a dependency (or, after this change, region) mutation is allowed "while `draft` or `reviewed`" to say "while `draft`" only - in `core/encounter.py` (`assign_dependency`/`unassign_dependency` docstrings), `cli/encounter.py` (`assign-dependency`/`unassign-dependency` command docstrings and the `Typer` app's top-level help text), and `mcp/encounter.py` (`encounter_assign_dependency`/`encounter_unassign_dependency` docstrings).
- Update `packages/crypts-and-commits/src/cac/core/templates/docs/workflow.md` in the same change (per `workflow-doc-source-of-truth`): the "region assignment/unassignment and dependency assignment/unassignment are both only permitted while `draft` or `reviewed`" line, the "Encounter -> Region" and "Encounter -> Encounter" connection bullets that still say "draft or reviewed", and the `draft -> reviewed` row of the status-lifecycle table (add a note that review now requires at least one assigned region).
- Update the packaged skill templates `templates/skills/{claude,codex}/campaign_manager/SKILL.md` in the same change (this is a procedure change, not just wording - CLAUDE.md requires both to move together): the "Dependencies may be assigned or unassigned while an encounter is `draft` or `reviewed`" sentence in both flavors needs to say "`draft`" only, and the Encounter Lifecycle's `draft` section should note that at least one region must be assigned before `encounter_review` will succeed. These are template edits only - this repo's own deployed `.claude/skills/`/`.agents/skills/` copies are never hand-edited (per `skills-authored-only-in-templates`); the developer redeploys via `cac bootstrap init` afterward.
- Update every existing test across `tests/core/test_encounter.py`, `tests/mcp/test_encounter.py`, `tests/cli/test_encounter.py`, `tests/core/test_campaign.py`, and `tests/cli/test_campaign.py` that currently calls review (directly or via a shared setup helper) without first assigning a region, since all of them will now fail the new gate. Two existing tests are no longer valid under the tightened mutation window and must be deleted or repurposed rather than patched: `test_region_changes_are_allowed_while_reviewed` and `test_dependency_changes_are_allowed_while_reviewed` (in `tests/core/test_encounter.py`) assert behavior (`reviewed` still allows mutation) that is now false. The corresponding `test_region_changes_are_rejected_after_reviewed`/`test_dependency_changes_are_rejected_after_reviewed` parametrized tests must add `"reviewed"` to their `terminal_status` cases, since mutation is now rejected starting at `reviewed`, not only after it.
- Also fix `tests/cli/test_encounter.py::test_assign_region_rejected_once_open` (added by the prior encounter in this campaign): it currently reviews an encounter with no region assigned, which will now fail before it ever reaches `open`. It needs a region assigned before `review`, and its actual assertion (assign fails once past `draft`) needs a *second* region to attempt assigning post-open, since the first is already attached pre-review.

## Rationale

The previous encounter in this campaign (`restrict-region-assignment-to-draft-reviewed`) closed the asymmetry between region and dependency mutation windows, but left a gap the campaign's stated problem (`region assignment is frequently skipped when creating/reviewing encounters`) still doesn't fully close: an encounter can still reach `reviewed` - and therefore `open` - with zero regions assigned, because nothing *requires* one. Restricting *when* a region can be assigned doesn't ensure *that* it ever is.

Requiring at least one region before `encounter_review` succeeds makes region assignment a hard precondition of the same gate that already enforces lore review, dependency completeness-at-open, and locked planning sections - turning "should assign a region" into "cannot get reviewed without one." This is a natural, minimal extension of the existing gate rather than a new mechanism.

Once that requirement exists, allowing regions (or dependencies, by the same logic established last encounter) to still be edited during `reviewed` undermines the guarantee the gate is meant to provide: the independent reviewer subagent checks the Plan against exactly the lore implied by the encounter's *current* region assignment at review time (per `prime_applicable_lore`). If regions could still change afterward, the reviewed plan and the lore it was actually checked against could silently diverge. Tightening the mutation window to `draft`-only closes that gap symmetrically for both regions and dependencies, and matches how the encounter's Requirements/Rationale/Plan/Verification already become immutable at the same transition.

## Plan

1. **`core/encounter.py`**
   - Add `class EncounterRegionRequiredError(ValueError)` alongside the other encounter exceptions (not a subclass of `EncounterRegionMutationError` - "must have one" and "can't change it now" are different failure modes).
   - In `review_encounter`, before delegating to `_transition`: load the post, and if its current status is `"draft"` and its `regions` list is empty, raise `EncounterRegionRequiredError` with a message naming the encounter and pointing at `assign_region`/`cac encounter assign-region`. Gate this on `status == "draft"` (mirroring `open_encounter`'s existing dependency-completeness check pattern) so an already-invalid transition still surfaces the normal `InvalidEncounterTransitionError` instead of a confusing region message.
   - Change `_REGION_MUTATION_STATUSES` and `_DEPENDENCY_MUTATION_STATUSES` to `frozenset({"draft"})`.
   - Update the `assign_dependency`/`unassign_dependency` docstrings ("while it is draft or reviewed" -> "while it is draft").

2. **`cli/encounter.py`**
   - Add `encounter_core.EncounterRegionRequiredError` to the `review` command's caught-exception tuple.
   - Update the `assign-dependency`/`unassign-dependency` command docstrings and the `Typer` app's top-level help text (the sentence "Dependencies may be changed while an encounter is 'draft' or 'reviewed'") to say `'draft'` only, and add a short mention that `review` now requires at least one assigned region.

3. **`mcp/encounter.py`**
   - No behavioral change needed for `encounter_review` (the new error propagates automatically). Update its docstring to mention the new region precondition, and update `encounter_assign_dependency`/`encounter_unassign_dependency` docstrings the same way as the CLI's.

4. **Tests - `tests/core/test_encounter.py`**
   - Add a small helper, e.g. `_assign_default_region(tmp_path, campaign, name, region_name="default-region")`, that creates the named region if it doesn't already exist and assigns it to the encounter - and a `_review(tmp_path, campaign, name, message="Reviewed.")` helper that calls `_assign_default_region` (only if the encounter has no regions yet) then `encounter.review_encounter(...)`. Replace direct `encounter.review_encounter(...)` calls that don't care about region specifics with `_review(...)`, including inside the parametrized `advance` lambda lists (`test_update_encounter_rejects_once_not_draft`, `test_abandon_encounter_succeeds_from_non_terminal_statuses`, `test_record_message_rejects_outside_reviewed_or_open`). Leave tests that assert on `review_encounter`'s own behavior in isolation (message-required, missing-encounter, rejects-when-not-draft, git-identity-error) calling `review_encounter` directly, since those need to control the region precondition explicitly (or, for the message/not-draft/missing/identity tests, assign a region first via `_assign_default_region` so the test still reaches the code path it's actually targeting).
   - Delete `test_region_changes_are_allowed_while_reviewed` and `test_dependency_changes_are_allowed_while_reviewed` (no longer true).
   - Add `"reviewed"` to the `terminal_status` parametrize list of `test_region_changes_are_rejected_after_reviewed` and `test_dependency_changes_are_rejected_after_reviewed` (both now need a region/dependency mutation attempted immediately after `review_encounter`, with no `open`/`complete`/`abandon` step, as one of the parametrized cases).
   - Add `test_review_encounter_requires_region` (raises `EncounterRegionRequiredError` when `regions` is empty) and `test_review_encounter_succeeds_with_region_assigned` (assign a region, then review succeeds).

5. **Tests - `tests/mcp/test_encounter.py`**
   - Same treatment: add an analogous helper (or inline `region.create_region` + `encounter.assign_region` before each `mcp_encounter.encounter_review(...)` call) everywhere a region isn't already part of the test's own setup. Add one test confirming `mcp_encounter.encounter_review` raises `EncounterRegionRequiredError` with no region assigned.

6. **Tests - `tests/cli/test_encounter.py`**
   - Same treatment via the CLI (`region create` + `assign-region` before `review`). Fix `test_assign_region_rejected_once_open` per the Requirements note above: assign `northlands` before reviewing, then after `open`, attempt to assign a second region (create one, e.g. `southlands`) and assert `exit_code == 1`. Add one test confirming `cac encounter review` on a region-less draft exits non-zero.

7. **Tests - `tests/core/test_campaign.py` and `tests/cli/test_campaign.py`**
   - `core/test_campaign.py`'s shared `_open_encounter` helper: add a region create+assign before its `review_encounter` call (one change point covers every caller). `cli/test_campaign.py`'s three inline `create -> review -> open` sequences: add a `region create` + `assign-region` invocation before each `review` invocation.

8. Run `pdm run ruff format .` and `pdm run ruff check .` throughout implementation, not just at the end, per `clean-tests-and-lint`.

## Verification

- `pdm run pytest -q` passes in full, with no skips or deletions used to dodge a failure (deleting the two now-false `*_allowed_while_reviewed` tests is a legitimate correction of a test asserting behavior this encounter intentionally removes, not a dodge).
- `pdm run ruff check .` reports zero errors; `pdm run ruff format .` reports no diffs.
- Grep the full `packages/crypts-and-commits/src` and `templates/skills` trees for the literal phrase `draft` or `reviewed` (and its "`draft`/`reviewed`" and "reviewed` or `draft`" variants) to confirm no stale mutation-window wording remains anywhere it described region or dependency mutation.
- Read the updated `workflow.md` and both `campaign_manager/SKILL.md` templates by eye to confirm they accurately describe: (a) region assignment is required before `encounter_review` succeeds, and (b) both region and dependency mutation are now `draft`-only.
- Per the deviation logged on the prior encounter, no separate manual `pdm run cac` walkthrough is planned here either - the automated core/mcp/cli tests added above exercise the same paths end-to-end.

## Log

### Review - 2026-07-28T04:45:28Z - John Hoff

Reviewed against clean-tests-and-lint, cli-mcp-parity, console-best-practices, skills-authored-only-in-templates, and workflow-doc-source-of-truth (all applicable via the crypts-and-commits region). The core/CLI/MCP implementation is sound and correctly mirrors the existing `open_encounter` dependency-completeness-check pattern for the new `EncounterRegionRequiredError` precondition; cli-mcp-parity is satisfied since no new command is added and the MCP error-propagation claim checks out against the actual code. One gap: the Plan's SKILL.md template edit list (both claude and codex flavors) names only the 'Dependencies may be assigned or unassigned while draft or reviewed' sentence in the Encounter Lifecycle section but misses a second, separate sentence in the same files' MCP-tool-forms section (`encounter_assign_dependency`/`encounter_unassign_dependency` — 'while the dependent encounter is draft or reviewed') that will also go stale under the narrowed draft-only window; the Plan's own Verification grep step across templates/skills should catch this, but the implementer should update it proactively rather than relying on Verification alone to surface it.

### Completed - 2026-07-28T05:02:17Z - John Hoff

Implemented, tested (693 passed, ruff clean), workflow.md and both campaign_manager/SKILL.md templates updated, project-wide grep for stale "draft or reviewed" wording confirmed clean.
