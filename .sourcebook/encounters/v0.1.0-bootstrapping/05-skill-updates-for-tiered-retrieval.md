---
campaign: v0.1.0-bootstrapping
created_by: John Hoff
created_on: '2026-07-25T01:22:30Z'
name: 05-skill-updates-for-tiered-retrieval
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-07-25T03:00:01Z'
---

# Skill Updates for Tiered Retrieval

## Requirements

- Update the `world-manager` and `campaign-manager` skills to drive the new tiered retrieval: use the single prime call for orientation, then the disclosure ladder (task -> region full + region lore summaries -> hydrate specific lore bodies for the review).
- The traversal PROCEDURE (the ladder) lives in the skill text — authored once, static — not in any tool payload, to avoid per-call token churn.
- `world-manager` owns static aggregation + prime; `campaign-manager` invokes prime as step one of work and appends active-campaign context.
- Leave a clean seam for encounter search: do NOT reference a search capability that does not yet exist (encounter search is deferred; see `docs/encounter-search-design.md`).
- Skill-only change: no `cac` Python code is modified (mirrors the `independent-review-subagent` skill-only precedent).
- Update `campaign-manager`'s draft -> reviewed gate so that once the reviewer subagent returns its findings, the skill automatically records that returned review as the `cac encounter review --message` content and transitions the encounter, without a separate human-approval pause at that step. Any feedback or requested changes the user has in response to the review must be captured with `cac encounter record-message`, not by reopening or re-drafting the Plan.

## Rationale

Per `docs/context-management-design.md` (the disclosure ladder and the skill ownership split). Encoding the "how to traverse" once in the skill, while tools return only the data traversed on, is the specific mechanism that keeps the prime lean and avoids re-sending procedural prose on every call. Depends on the prime/applicable-lore/budget capabilities (encounters 03-04) existing.

**Region note:** this encounter's assignment to `crypts-and-commits` (path `packages/crypts-and-commits`) is technically correct today only because skills' source of truth is currently their installation location, `.claude/skills/`. Once skills' source of truth moves into the `crypts-and-commits` package itself (planned, to support bootstrapping the skills into other projects), this region assignment should be revisited to cover wherever that templated source lives instead.

## Plan

1. Update `.claude/skills/world-manager/SKILL.md`: document the prime call and the disclosure ladder; state summaries-route / bodies-are-ground-truth for review.
2. Update `.claude/skills/campaign-manager/SKILL.md`: prime as step one; no search references yet. Rewrite the draft -> reviewed gate: once the reviewer subagent returns its findings and proposed message, the skill itself runs `cac encounter review --message "<subagent's returned review>"` automatically **only when the verdict is PASS-WITH-NOTES** — no separate human-approval pause before that transition. On REJECT or NOT-REVIEWABLE, preserve the existing behavior: do not transition, relay the reviewer's reasons, revise the draft, and spawn a fresh reviewer again. Document `cac encounter record-message` as the mechanism for any user feedback or requested changes made in response to a PASS-WITH-NOTES review, instead of reopening or re-drafting the Plan.
3. Keep wording free of hardcoded self-paths (portability for the eventual move into `templates/skills`).
4. Content review + `clean-tests-and-lint` (trivially, no Python changes).

## Verification

- The two `SKILL.md` files describe the tiered-retrieval flow, the disclosure ladder in-skill, the ownership split, and leave the search seam unfilled.
- `pdm run pytest -q` and `ruff check`/`format` clean (no Python change).

## Log

### Review - 2026-07-25T02:51:17Z - John Hoff

Reviewed against both applicable lore items. clean-tests-and-lint (world-assigned) is honored -- the Plan keeps the pytest/ruff gate even though no Python is touched. console-best-practices (region-assigned via crypts-and-commits) is not triggered since the change is skill-only and never touches cac/cli/* Console output; no conflict. Two notes were resolved before transition: (1) the Plan's auto-transition on reviewer completion now explicitly applies only on a PASS-WITH-NOTES verdict, preserving the existing REJECT/NOT-REVIEWABLE revise-and-re-review loop; (2) the encounter's region assignment (crypts-and-commits, packages/crypts-and-commits) is technically correct today only because skills' source of truth is currently their installation location (.claude/skills/) -- a note was added to the Rationale flagging that this should be revisited once skills' source of truth moves into the crypts-and-commits package for bootstrapping. Verdict: PASS-WITH-NOTES.

### Completed - 2026-07-25T03:00:01Z - John Hoff

world-manager and campaign-manager SKILL.md updated for the tiered-retrieval disclosure ladder (cac prime get / cac prime applicable-lore), the PASS-WITH-NOTES auto-transition on the draft->reviewed gate with REJECT/NOT-REVIEWABLE loop preserved, and record-message as the post-review feedback channel. pytest -q (465 passed) and ruff check/format clean; no Python changed.
