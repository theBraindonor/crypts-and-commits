---
campaign: v0.1.0-bootstrapping
created_by: John Hoff
created_on: '2026-07-25T01:22:30Z'
name: 05-skill-updates-for-tiered-retrieval
regions:
- crypts-and-commits
status: draft
updated_by: John Hoff
updated_on: '2026-07-25T01:23:03Z'
---

# Skill Updates for Tiered Retrieval

## Requirements

- Update the `world-manager` and `campaign-manager` skills to drive the new tiered retrieval: use the single prime call for orientation, then the disclosure ladder (task -> region full + region lore summaries -> hydrate specific lore bodies for the review).
- The traversal PROCEDURE (the ladder) lives in the skill text — authored once, static — not in any tool payload, to avoid per-call token churn.
- `world-manager` owns static aggregation + prime; `campaign-manager` invokes prime as step one of work and appends active-campaign context.
- Leave a clean seam for encounter search: do NOT reference a search capability that does not yet exist (encounter search is deferred; see `docs/encounter-search-design.md`).
- Skill-only change: no `cac` Python code is modified (mirrors the `independent-review-subagent` skill-only precedent).

## Rationale

Per `docs/context-management-design.md` (the disclosure ladder and the skill ownership split). Encoding the "how to traverse" once in the skill, while tools return only the data traversed on, is the specific mechanism that keeps the prime lean and avoids re-sending procedural prose on every call. Depends on the prime/applicable-lore/budget capabilities (encounters 03-04) existing.

## Plan

1. Update `.claude/skills/world-manager/SKILL.md`: document the prime call and the disclosure ladder; state summaries-route / bodies-are-ground-truth for review.
2. Update `.claude/skills/campaign-manager/SKILL.md`: prime as step one; no search references yet.
3. Keep wording free of hardcoded self-paths (portability for the eventual move into `templates/skills`).
4. Content review + `clean-tests-and-lint` (trivially, no Python changes).

## Verification

- The two `SKILL.md` files describe the tiered-retrieval flow, the disclosure ladder in-skill, the ownership split, and leave the search seam unfilled.
- `pdm run pytest -q` and `ruff check`/`format` clean (no Python change).
