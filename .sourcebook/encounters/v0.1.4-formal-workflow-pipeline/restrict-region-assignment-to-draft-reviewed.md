---
campaign: v0.1.4-formal-workflow-pipeline
created_by: John Hoff
created_on: '2026-07-28T03:32:12Z'
depends_on: []
name: restrict-region-assignment-to-draft-reviewed
regions:
- crypts-and-commits
status: draft
updated_by: John Hoff
updated_on: '2026-07-28T03:32:20Z'
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

Plan has not been described yet.

## Verification

Verification has not been described yet.
