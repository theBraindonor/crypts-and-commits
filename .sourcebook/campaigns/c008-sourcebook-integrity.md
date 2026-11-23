---
archived: false
bosses:
- b003-sourcebook-integrity
created_by: John Hoff
created_on: '2026-11-23T21:55:46Z'
name: c008-sourcebook-integrity
status: open
updated_by: John Hoff
updated_on: '2026-11-23T21:57:37Z'
---

# c008: Sourcebook integrity

## Objective

Vanquish b003-sourcebook-integrity by closing two gaps where links between sourcebook records can only be kept consistent by developer hand-edits, or not at all:

1. **Goal adoption:** an `open` or `paused` campaign that has not been reactivated can adopt existing unassigned bosses through a guarded, logged operation.
2. **Referenced deletes:** `lore_delete`, `region_delete` and `campaign_delete` refuse while a live (unarchived) record references the target, and list every referrer.

## Starting point

- Boss membership changes only through `coupling.set_bosses` (draft-only, message required, `_eligible` = `available` + prerequisites satisfied via `boss_candidates.assess`, reciprocal `Links` validation, `Recovery`-wrapped writes, campaign `Log` entry). c001 needed a GM-override hand-edit to link b001/b002 after opening (c001/e025). The planning and development workflow guides call open-campaign adoption "deferred".
- `lore.delete_lore` and `region.delete_region` delete unconditionally. `campaign.delete_campaign` goes through `@coupling.campaign_operation("delete")`, which already refuses while bosses are linked (`CampaignLinkedError`). Deleting lore or regions leaves dangling names in world/region `assigned_lore`, lore `assigned_regions` and encounter `regions` (a CLAUDE.md "known limitation").
- `campaign_reactivate` reopens a completed campaign with a `Reactivated` log entry; nothing in frontmatter marks a campaign as reactivated today.

## Tactics

- **e001: open-campaign goal adoption.** A new core operation (e.g. `coupling.adopt_bosses(root, name, bosses, message)`), reusing `set_bosses`'s pattern and `_eligible` exactly:
  - The campaign must be `open`/`paused`, unarchived and not reactivated.
  - Adoption only adds; same-set requests are read-only.
  - Message required; a `Bosses adopted` log entry is written.
  - Reciprocal links are validated and every written record is stamped, with atomic recovery.

  Choose and test how "reactivated" is detected. Expose it as `campaign_adopt_bosses` over MCP and `cac campaign adopt-bosses` over CLI (parity). Update `tool-reference.md`, the owning phase guides (remove the "adoption is deferred" language), and both campaign-manager skill flavors in the templates. Deployed copies are left alone; redeploying is the developer's job.
- **e002: refuse referenced deletes.** One core referrer inventory per target type, listing every referrer in the error.
  - **Lore:** world `assigned_lore`, region `assigned_lore`.
  - **Region:** lore `assigned_regions`, region-scoped `assigned_lore` edges as recorded, unarchived encounters' `regions` in any status. Encounters under archived campaigns don't count.
  - **Campaign:** keep the existing boss guard, plus any other live referrer the inventory finds (e.g. rulings named `cNNN-…`, live encounters).

  Settle b003's last open question, the exact referrer list per type, in the e002 plan. Keep CLI/MCP error parity. Update `tool-reference.md` and the phase guides, and drop the "known limitation" line from CLAUDE.md if the developer approves.
- e002 does not depend on e001. They touch separate operations and can run in either order; e001 goes first because it carries the procedural doc and skill changes.

## Regions

`crypts-and-commits` (lore: `cli-mcp-parity`, `console-best-practices`, `skills-authored-only-in-templates`, `workflow-doc-source-of-truth`), plus world lore `clean-tests-and-lint`.

## Out of scope

- Cascade cleanup of references (the developer chose refusal).
- Removing members from an open campaign, or adopting into a reactivated, completed or abandoned campaign.
- Repairing historical hand-edited links from c001.

## Log
