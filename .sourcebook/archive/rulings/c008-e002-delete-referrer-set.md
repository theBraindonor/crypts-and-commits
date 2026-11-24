---
archived: true
campaign: c008-sourcebook-integrity
created_by: John Hoff
created_on: '2026-11-23T23:32:47Z'
encounter: e002-refuse-referenced-deletes
history:
- action: note
  by: John Hoff
  message: 'Triaged on planning, 2026-11-23, with the developer: no lore, region or
    world change is needed. The referrer set is data-model behavior enforced in core/referrers.py,
    and c008/e002 already documented it where it is owned: the tool-reference.md "Referenced
    deletes" section, the Connections bullet and campaign-deletion paragraph in both
    phase guides, the world-manager and campaign-manager skill templates, and CLAUDE.md
    (which replaced the old "known limitation"). It describes what deletes do, not
    a standing convention for reviewing new work, so lore would only duplicate it.'
  'on': '2026-11-24T00:12:13Z'
name: c008-e002-delete-referrer-set
origin: Developer (GM) answers on the c008/e002 referrer set, 2026-11-23, before drafting
  review; region/encounter rule from b003 planning decisions
resolution: 'Triaged on planning, 2026-11-23, with the developer: no lore, region
  or world change is needed. The referrer set is data-model behavior enforced in core/referrers.py,
  and c008/e002 already documented it where it is owned: the tool-reference.md "Referenced
  deletes" section, the Connections bullet and campaign-deletion paragraph in both
  phase guides, the world-manager and campaign-manager skill templates, and CLAUDE.md
  (which replaced the old "known limitation"). It describes what deletes do, not a
  standing convention for reviewing new work, so lore would only duplicate it.'
status: noted
summary: 'Referenced deletes refuse while any referrer exists. Lore: world/region
  assigned_lore. Region: lore assigned_regions plus unarchived encounters'' regions
  (archived-campaign encounters don''t block). Campaign: the existing boss guard plus
  any of its own encounters (live or archived) and any ruling naming it (live or archived),
  so a campaign with rulings is never deletable.'
updated_by: John Hoff
updated_on: '2026-11-24T00:12:14Z'
---

## Decision

`lore_delete`, `region_delete` and `campaign_delete` refuse while the target is referenced, listing every referrer:

- **Lore:** the world's `assigned_lore` and every region's `assigned_lore`.
- **Region:** every lore entry's `assigned_regions` and every unarchived encounter's `regions`, in any status. Encounters under archived campaigns are history and do not block (b003 planning decision, 2026-11-23).
- **Campaign:** the existing boss guard, plus every one of the campaign's own encounters, live or archived, and every ruling whose `campaign` names it, live or archived.

## Context

b003 left the exact referrer list per target open. For campaigns, the developer chose:
- any encounter blocks, because encounters are the campaign's children, not mere references, and an archived campaign's archived encounters would otherwise be orphaned. The alternative was blocking only on live encounters.
- any ruling blocks, live or archived. The alternatives were blocking only on recorded rulings, or never blocking.

## Consequences

- Rulings have no delete, so a campaign with any ruling is permanently undeletable. This is accepted as protecting decision history.
- Deleting a campaign with encounters requires deleting them first, which is only possible while the campaign is mutable and the encounters have no dependents.
- The referrer inventory lives in one core module, so future link types are added in one place.
