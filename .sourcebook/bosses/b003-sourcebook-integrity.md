---
archived: false
campaign: c008-sourcebook-integrity
created_by: John Hoff
created_on: '2026-11-20T23:43:29Z'
depends_on:
- b005-ruling-records
name: b003-sourcebook-integrity
status: available
summary: 'Close two sourcebook integrity gaps: let an open or paused (not reactivated)
  campaign adopt existing unassigned bosses through a guarded, logged operation using
  the same eligibility as draft selection (replacing the developer hand-edit c001
  needed), and make lore/region/campaign deletes refuse while referenced by live records,
  listing every referrer, instead of leaving dangling references.'
updated_by: John Hoff
updated_on: '2026-11-23T21:55:46Z'
---

## Goal

Remove two places where the sourcebook's links between records can only be kept consistent by developer hand-edits or not at all: campaign ownership of goals after a campaign has opened, and references left behind when a referenced record is deleted.

## Rationale

- **Goal adoption (r001):** campaign boss membership can only change while a campaign is `draft` (`campaign_set_bosses`), and `boss_record` never links a recorded goal to a campaign. c001-boss-edition opened before its goals existed as bosses, so linking b001/b002 required a GM override that hand-edited boss and campaign frontmatter (recorded in c001/e025). The planning and development workflow guides already name this as deferred ("adopting ownership into an already-open legacy campaign is deferred").
- **Referenced deletes (r002):** `lore_delete`, `region_delete` and `campaign_delete` leave dangling names in world/region `assigned_lore`, encounter `regions` and similar link lists, a known limitation recorded in CLAUDE.md. `campaign_delete` already refuses while bosses are linked, so refusal is the consistent model.

## Success Criteria

- A guarded adoption operation (e.g. `campaign_adopt_bosses(name, bosses, message)`) on an `open` or `paused` campaign that has not been reactivated: requires a nonblank message, logs the change on the campaign, validates reciprocal boss/campaign ownership, applies the same eligibility rule as draft selection (each adopted boss `available`, unassigned, with every prerequisite satisfied), and stamps every written record. Adopted bosses' designs freeze on link, exactly as with selection. Adoption only adds; it never removes existing members.
- `lore_delete`, `region_delete` and `campaign_delete` refuse while the target is referenced by a live (unarchived) record, and the error lists every referrer so the developer can unassign first.
- CLI and MCP parity for every new or changed operation (`cli-mcp-parity`).
- `templates/docs/planning-workflow.md`, `templates/docs/development-workflow.md` (and the `workflow.md` routing index if affected) and `templates/docs/tool-reference.md` describe the new behavior per `workflow-doc-source-of-truth`; the "adoption is deferred" language is removed; campaign-manager skill templates (both flavors) updated where procedure changes.
- Tests cover the new guards; `pdm run pytest -q` and ruff are clean.

## Design Notes

Promoted from r001-open-campaign-adopts-goals and r002-cascade-clean-deleted-references during planning, 2026-11-20. The developer chose a single integrity goal and the refuse-while-referenced direction over cascade cleanup.

Planning decisions, 2026-11-23 (developer-confirmed):

- **Adoption eligibility:** same as selection — reuse the draft-selection eligibility check (`coupling._eligible`: `available` + prerequisites satisfied via `boss_candidates.assess`). No co-adoption special case; adopt prerequisites first in a separate call if needed.
- **Adoption scope:** generally allowed on `open`/`paused` campaigns, not limited to legacy/bossless ones. Refused on a campaign that has been reactivated (`campaign_reactivate`) for pre-merge review fixes — adding goals there is scope creep. How "reactivated" is detected (e.g. the campaign's `Reactivated` log entry vs. a new frontmatter flag) is an encounter-level design choice.
- **Encounter-region links:** unarchived encounters, in any status, count as referrers and block `region_delete` (applicable-lore resolution reads them). Encounters under archived campaigns are history and do not block.

## Open Questions

- Which other link lists count as referrers for each delete (inventory to be confirmed during encounter planning: world/region `assigned_lore`, lore `assigned_regions`, encounter `regions`, campaign `bosses`/boss `campaign`, rulings' cNNN names)?
