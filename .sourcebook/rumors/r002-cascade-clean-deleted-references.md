---
archived: false
boss: null
created_by: John Hoff
created_on: '2026-10-28T17:53:44Z'
history: []
name: r002-cascade-clean-deleted-references
origin: Known limitation recorded in this repository's CLAUDE.md ("deleting a lore/region/campaign
  entry does not cascade-clean stale references").
resolution: null
status: open
summary: Deleting a lore, region or campaign entry leaves stale references in records
  that pointed at it; consider cascade cleanup or a guarded refusal with a clear list
  of referrers.
updated_by: John Hoff
updated_on: '2026-10-28T17:53:44Z'
---

Today `lore_delete`, `region_delete` and `campaign_delete` remove the record but leave dangling names behind: world and region `assigned_lore`, encounter `regions`, and similar link lists. Later reads either skip or trip over the missing target.

Two directions to weigh:
- **Cascade cleanup:** remove the dangling references in the same guarded, recoverable write cohort, with each changed record stamped.
- **Refuse while referenced:** fail the delete and list every referrer, so the developer unassigns first.

Campaign deletion already refuses when bosses are linked, which suggests refusal is the consistent model for anything carrying history. Encounter-to-region links might be better left as historical facts.
