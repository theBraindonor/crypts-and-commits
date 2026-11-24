---
archived: true
campaign: c008-sourcebook-integrity
created_by: John Hoff
created_on: '2026-11-23T22:49:27Z'
encounter: e001-open-campaign-goal-adoption
history:
- action: note
  by: John Hoff
  message: 'Triaged on planning, 2026-11-23, with the developer: no lore, region or
    world change is needed. The decision is implementation behavior, and c008/e001
    already wrote it into the packaged docs that own it: tool-reference.md (the campaign
    `reactivated` flag and the adopt-bosses guards), migration-guide.md (campaigns
    reactivated by older libraries are not detected) and the Reactivation bullet in
    both phase guides. It sets no review convention for future encounters.'
  'on': '2026-11-24T00:12:11Z'
name: c008-e001-reactivated-frontmatter-flag
origin: Developer (GM) answer to the c008/e001 plan choice, 2026-11-23, before independent
  review
resolution: 'Triaged on planning, 2026-11-23, with the developer: no lore, region
  or world change is needed. The decision is implementation behavior, and c008/e001
  already wrote it into the packaged docs that own it: tool-reference.md (the campaign
  `reactivated` flag and the adopt-bosses guards), migration-guide.md (campaigns reactivated
  by older libraries are not detected) and the Reactivation bullet in both phase guides.
  It sets no review convention for future encounters.'
status: noted
summary: 'A campaign counts as reactivated (and so refuses campaign_adopt_bosses)
  through a persistent `reactivated: true` frontmatter flag set by campaign_reactivate
  and never cleared. An absent flag means false, so no migration is needed. The Log
  text is not parsed. Campaigns reactivated before the flag existed are not detected;
  none is open.'
updated_by: John Hoff
updated_on: '2026-11-24T00:12:14Z'
---

## Decision

A campaign that has been reactivated is identified by a persistent frontmatter flag, `reactivated: true`. `campaign_reactivate` sets it, and nothing clears it, including a later re-completion. `campaign_adopt_bosses` refuses any campaign where the flag is true. An absent flag reads as false.

## Context

b003's planning decisions refuse goal adoption on a campaign reactivated for pre-merge review fixes, and leave the detection method to the encounter. Before this change the only trace of reactivation was a `### Reactivated` entry in the campaign body's Log. The alternatives were:
- parsing that Log heading;
- doing both, so historical reactivations would also be caught.

## Consequences

- Guards keep reading frontmatter, never body prose.
- The flag is additive: no schema migration, and existing campaigns read as not reactivated.
- A campaign reactivated before this change and still open would not be detected. None exists today, and tool-reference documents the limitation.
- Like the reactivation status itself, the flag is visible in campaign metadata.
