---
archived: false
campaign: c002-rulings
created_by: John Hoff
created_on: '2026-11-21T03:43:43Z'
encounter: e006-ruling-guides-and-public-docs
history: []
name: c002-e006-region-text-in-scope
origin: Developer (John Hoff), during c002/e006 execution
resolution: null
status: recorded
summary: Fix the crypts-and-commits region body's stale core/ module list (add ruling.py)
  inside e006 with the summary unchanged, rather than deferring it as a rumor. Stale
  priming text is fixed in the docs encounter that finds it.
updated_by: John Hoff
updated_on: '2026-11-21T03:43:43Z'
---

## Decision

The independent review of e006 noted that the `crypts-and-commits` region body still listed the `core/` modules without `ruling.py`. The encounter's plan did not cover that region text. The developer chose option (a): update the region body inside e006 with `region_update`, adding `ruling.py` to the module list and keeping the region summary word for word. Option (b), capturing it as a rumor for planning, was declined.

## Context

e006 already updated the world summary's domain model and `CLAUDE.md`'s architecture list for rulings. The region body is the same kind of priming text, and the summary does not list modules, so no summary re-approval was needed.

## Consequences

The region and `CLAUDE.md` module lists now agree. The change was recorded in e006's log as a deviation approved by the developer, not as part of the reviewed plan.
