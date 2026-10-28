---
archived: false
campaign: c001-boss-edition
created_by: John Hoff
created_on: '2026-10-28T17:42:54Z'
depends_on:
- b001-boss-records
name: b002-rumor-records
status: vanquished
summary: 'Standalone rumor records: numbered rNNN backlog notes ("we think X should
  be done") captured from anywhere on any branch with a free-text origin, triaged
  on planning by renumbering collisions, promoting to unassigned bosses (link stored
  only on the rumor), or dismissing; reopen, archive, no delete; own search type.'
updated_by: John Hoff
updated_on: '2026-10-28T22:42:24Z'
---

## Goal

Give CAC a backlog for ideas that are not yet goals: a place to capture "we think X should be done" from anywhere, and a planning-side path that turns those notes into bosses or dismisses them with a reason.

## Rationale

The first design tied rumors to a single per-campaign document, which made them a strict output of execution. Most good ideas come from elsewhere (operating the project, reviews, other people), and each needs its own identity so planning can triage it, link it to a goal, dismiss it, or notice how often it recurs.

## Success Criteria

- `rumors/rNNN-slug.md` records with summary, free-text origin and optional body; `rNNN` short refs.
- Lifecycle `open` -> `promoted` (linked to an unassigned proposed/available boss, recorded only on the rumor, many rumors per boss) or `dismissed` (reason required); `reopen`; `archive`; transition `history`; no delete.
- `rumor_renumber` fixes cross-branch number collisions on planning for open or dismissed rumors only; promoted numbers are settled.
- Nine `rumor_*` MCP tools and `cac rumor` commands; rumor search type; not in prime.
- Owning docs, skills, guides and repo instructions describe the model.

## Design Notes

Delivered by campaign c001-boss-edition (e023-e024, public docs in the closeout encounter). Depends on b001-boss-records because promotion targets bosses. Linked to c001 by the same developer (GM) override as b001.

## Open Questions

None for this release.
