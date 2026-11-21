---
archived: true
campaign: c002-rulings
created_by: John Hoff
created_on: '2026-11-21T03:47:16Z'
encounter: e007-canonize-targets-lore-region-world
history:
- action: canonize
  by: John Hoff
  message: Verified world_get already describes ruling canonization as a narrative
    of lore, region or world changes. The standing world summary and the c002/e007
    guidance alignment embody the developer's decision that any of those three context
    types may be updated; dispositions remain narrative without formal target links.
    This supersedes the narrower lore-only wording in b005's frozen summary, which
    is preserved as historical design text. No additional world edit is needed.
  'on': '2026-11-21T04:33:52Z'
name: c002-e007-canonize-targets-lore-region-world
origin: Developer (John Hoff), reviewing c002 before campaign completion
resolution: Verified world_get already describes ruling canonization as a narrative
  of lore, region or world changes. The standing world summary and the c002/e007 guidance
  alignment embody the developer's decision that any of those three context types
  may be updated; dispositions remain narrative without formal target links. This
  supersedes the narrower lore-only wording in b005's frozen summary, which is preserved
  as historical design text. No additional world edit is needed.
status: canonized
summary: Canonizing a ruling may target lore, a region or the world (ruling -> lore
  | region | world), not only lore. The narrative names whatever was updated; there
  are still no formal links. Supersedes the lore-only wording in b005's frozen summary.
updated_by: John Hoff
updated_on: '2026-11-21T04:33:52Z'
---

## Decision

The developer expanded the canonize path from ruling → lore to **ruling → (lore | region | world)**. When planning canonizes a ruling, the standing change may be a lore entry, a region record (body, summary, path or lore assignment) or the world summary or settings, and the canonize narrative records which.

## Context

This came up while reviewing c002 before completing the campaign. Core, the CLI/MCP contracts, `workflow.md`, `tool-reference.md` and the world-planner procedure already allowed any world change. Some prose narrowed it to lore: the world-planner skill descriptions, a `workflow.md` sentence on links, several public docs, and `b005-ruling-records`' summary ("canonized (how the lore was updated) or noted (why it needs no lore)"). b005 is frozen now that it is assigned, so it is not edited. Its body already describes canonizing as updating "the world (lore, regions, world summary)".

## Consequences

- Encounter c002/e007 aligns the remaining lore-only wording; there is no behavior change.
- Dispositions stay narrative only, with no formal ruling-to-lore, -region or -world links (b005's design choice stands).
- Planners should canonize region and world decisions, such as `c002-e006-region-text-in-scope`, rather than inventing lore for them or noting them by default.
