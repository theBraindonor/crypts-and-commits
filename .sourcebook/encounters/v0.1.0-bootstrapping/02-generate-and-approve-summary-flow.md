---
campaign: v0.1.0-bootstrapping
created_by: John Hoff
created_on: '2026-07-25T01:22:25Z'
name: 02-generate-and-approve-summary-flow
regions:
- crypts-and-commits
status: draft
updated_by: John Hoff
updated_on: '2026-07-25T01:22:59Z'
---

# Generate-and-Approve Summary Flow

## Requirements

- When a region's or lore's body is created or edited, a summary is (re)generated and the GM approves (or edits) it before the change commits — the generate-and-approve model.
- The summary must never be stale relative to the body: regeneration is wired into the same edit transition/hook that writes the body (and stamps `updated_on`), so a body change cannot commit without an accompanying current summary.
- Respect the 500-character cap established in encounter 01.
- The drafting mechanism (see Rationale) is chosen and documented as part of this encounter.

## Rationale

Per `docs/context-management-design.md` (Resolved decision #1). Summaries are a governance-adjacent artifact — lore summaries route the review gate — so a human approval gate is retained rather than silent auto-generation. Tying regeneration to the write transition is what makes the "never stale" guarantee real, using the same write-path ownership CAC already relies on for `updated_on` stamping. This builds the workflow on top of the storage established in encounter 01.

Open sub-decision to resolve in draft: what "the tool drafts" means in the current CLI, which has no in-process LLM. Candidates: (a) the calling agent supplies a proposed summary that the GM approves; (b) deterministic extraction (e.g., leading text up to the cap) as a starting draft; (c) editor pre-fill. True model-generated drafting likely arrives with the MCP/agent surface (encounter 06). Pick one and document it.

## Plan

1. `core/lore.py`, `core/region.py`: hook summary (re)generation + approval into the create/update path; guarantee a body write carries a current summary.
2. `cli/lore.py`, `cli/region.py`: the approval interaction (approve/edit the draft) around the chosen drafting mechanism.
3. Enforce the cap and reuse encounter 01's storage + placeholder.
4. Tests mirror source: regeneration-on-edit, approval, cap, and the never-stale invariant.
5. `clean-tests-and-lint`.

## Verification

- `pdm run pytest -q` and `ruff check`/`format` clean, with coverage for regeneration-on-edit, approval, cap, and never-stale.
- Editing a region/lore body triggers summary (re)generation and requires approval before commit; the stored summary reflects the new body.
- The 500-char cap and placeholder behavior from encounter 01 still hold.
