---
archived: false
created_by: John Hoff
created_on: '2026-11-20T23:43:29Z'
depends_on:
- b005-ruling-records
name: b003-sourcebook-integrity
status: proposed
summary: 'Close two sourcebook integrity gaps: let an open or paused campaign adopt
  existing unassigned bosses through a guarded, logged operation (replacing the developer
  hand-edit c001 needed), and make lore/region/campaign deletes refuse while referenced,
  listing every referrer, instead of leaving dangling references.'
updated_by: John Hoff
updated_on: '2026-11-21T00:04:49Z'
---

## Goal

Remove two places where the sourcebook's links between records can only be kept consistent by developer hand-edits or not at all: campaign ownership of goals after a campaign has opened, and references left behind when a referenced record is deleted.

## Rationale

- **Goal adoption (r001):** campaign boss membership can only change while a campaign is `draft` (`campaign_set_bosses`), and `boss_record` never links a recorded goal to a campaign. c001-boss-edition opened before its goals existed as bosses, so linking b001/b002 required a GM override that hand-edited boss and campaign frontmatter (recorded in c001/e025). The workflow guide already names this as deferred ("adopting ownership into an already-open legacy campaign is deferred").
- **Referenced deletes (r002):** `lore_delete`, `region_delete` and `campaign_delete` leave dangling names in world/region `assigned_lore`, encounter `regions` and similar link lists, a known limitation recorded in CLAUDE.md. `campaign_delete` already refuses while bosses are linked, so refusal is the consistent model.

## Success Criteria

- A guarded adoption operation (e.g. `campaign_adopt_bosses(name, bosses, message)`) on an `open` or `paused` campaign: requires a message, logs the change on the campaign, validates reciprocal boss/campaign ownership and eligibility, and stamps every written record.
- `lore_delete`, `region_delete` and `campaign_delete` refuse while the target is referenced, and the error lists every referrer so the developer can unassign first.
- CLI and MCP parity for every new or changed operation (`cli-mcp-parity`).
- `templates/docs/workflow.md` and `templates/docs/tool-reference.md` describe the new behavior; the "adoption is deferred" language is removed; skills updated in the packaged templates where procedure changes.
- Tests cover the new guards; `pdm run pytest -q` and ruff are clean.

## Design Notes

Promoted from r001-open-campaign-adopts-goals and r002-cascade-clean-deleted-references during planning, 2026-11-20. The developer chose a single integrity goal and the refuse-while-referenced direction over cascade cleanup.

## Open Questions

- Adoption: should it require prerequisite eligibility as selection does, or allow co-adopted prerequisites?
- Adoption: limit it to legacy or first campaigns, or allow it generally on open/paused campaigns?
- Adoption: how does it interact with the design-freeze rule and with `campaign_reactivate`?
- Deletes: should encounter-to-region links block a region delete, or be treated as historical facts that don't count as referrers?
