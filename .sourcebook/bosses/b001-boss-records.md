---
archived: false
created_by: John Hoff
created_on: '2026-10-28T17:42:49Z'
depends_on: []
name: b001-boss-records
status: available
summary: 'Boss Edition core: bosses as managed project goals (proposed/available/withdrawn/vanquished,
  archive, graph-validated prerequisites, candidates, roadmap recording), numbered
  names and short refs, boss-campaign promotion and coupled lifecycle with multi-boss
  campaigns and reactivation, active bosses in prime, boss search, and the planning
  skill, branch workflow and guides.'
campaign: c001-boss-edition
updated_by: John Hoff
updated_on: '2026-10-28T17:42:57Z'
---

## Goal

Give CAC a first-class way to capture and refine project goals ("bosses") before any campaign commits to them, and tie bosses, campaigns and encounters together through numbered names and a planning/assignment/execution branch workflow.

## Rationale

Before Boss Edition, the only planning unit was the campaign: goals had no identity of their own, could not be refined or ordered by prerequisites before work started, and nothing recorded why a campaign existed or when its goal was achieved. Bosses separate "what we want" from "how this campaign gets it".

## Success Criteria

- Boss records with `proposed` -> `available` -> `vanquished` (only by completing the owning campaign) or `withdrawn`, archival, and graph-validated `depends_on`.
- `boss_candidates` explains eligibility and blockers; `boss_record` adopts existing roadmap goals with immutable provenance.
- Numbered names (`bNNN`, `cNNN`, `cNNN/eNNN`) with short-ref resolution; skills allocate, core never does.
- Promotion (`boss_assign_campaign`, multi-boss `campaign_create`), frozen designs once linked, coupled complete/abandon/reactivate/archive, and `campaign_reactivate` for pre-merge fixes.
- Prime exposes active bosses; bosses have their own search type.
- world-planner skill, campaign-manager updates, world branch settings, the Branching Guide and Migration Guide; endpoints stay branch-agnostic.
- CLI `--body-file` everywhere and the narrower Codex `apply_patch` hook.

## Design Notes

Delivered by campaign c001-boss-edition (e001-e022). Linked to c001 by a developer (GM) override after c001 opened, so its completion vanquishes this goal; see the c001 log and the encounter recording the override.

## Open Questions

None for this release. Follow-ups are captured as rumors.
