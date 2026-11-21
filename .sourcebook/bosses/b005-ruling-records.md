---
archived: false
created_by: John Hoff
created_on: '2026-11-21T00:04:48Z'
depends_on: []
name: b005-ruling-records
status: proposed
summary: 'Add rulings: ADR-style records of developer (GM)-confirmed decisions made
  during active development, named cNNN-eNNN-slug after the campaign/encounter where
  they were made (e000 for campaign-level). Recorded rulings appear in prime; planning
  gives every ruling a disposition with hindsight: canonized into lore (link kept
  on the ruling) or noted and archived.'
updated_by: John Hoff
updated_on: '2026-11-21T00:04:48Z'
---

## Goal

Give the decisions made during development an identity and a lifecycle, so that planning can review them with hindsight and decide which ones become standing lore. A rumor captures what we might do; a ruling captures what the developer (Game Master) decided while doing it.

## Rationale

Coding assistants working on CAC-driven projects keep recommending architecture decision records (ADRs). Today, developer decisions are scattered across encounter messages, boss design notes, rumor resolutions and GM-override logs, with no way to find them again or to promote them into lore. Whether a decision matters beyond its moment is often unknowable when it is made; the important ones only become clear in hindsight. Rumors already prove the pattern of capturing freely during work and dispositioning deliberately during planning. Lore remains the authority enforced by reviews; rulings become its intake and audit trail.

## Scope and model

- **Rulings belong to active development.** A ruling is always captured within a campaign, and is named for the campaign and encounter in which it was made: `cNNN-eNNN-slug`, using `e000` when the decision was made at campaign level with no open encounter. Outside an active campaign there is no ruling; the appropriate capture is a rumor.
- **Capture trigger.** A ruling records an answer to an open question or choice (a boss's open question, an encounter's open question, a plan choice, or the rationale for overriding a reviewer REJECT) that the developer confirmed. Capture is skill guidance that leans on the way agents already ask and resolve open questions with the developer; it is not a core-enforced rule.
- **Content.** A required summary, free-text origin, and a body recording the decision, its context and its consequences.
- **Lifecycle.** `recorded` (untriaged; the state of every new ruling) → `canonized` (reflected in one or more lore entries, link stored on the ruling) or `noted` (reason required; historical only, safe to ignore). Both dispositions are archivable. There is a reopen operation and a transition history, and no delete.
- **Prime.** Prime includes `recorded` rulings only. Canonized rulings live on through lore, and noted rulings can be ignored, so the recorded set is the decision record of the current branch's in-flight work.
- **Planning.** A well-run planning session gives every integrated recorded ruling a disposition: either it is canonized (creating or updating lore with developer approval) or it is noted and archived, in the same way rumors are promoted or dismissed.

## Success Criteria

- Ruling records with the naming, content and lifecycle above, created only within an existing campaign (and an existing encounter, unless `e000`).
- Full `ruling_*` MCP tools and matching `cac ruling` commands (`cli-mcp-parity`), a `ruling` search type, and prime exposure of recorded rulings.
- world-planner triages rulings alongside rumors, including the canonize-into-lore procedure. campaign-manager (and any skill working in an active campaign) captures rulings when the developer confirms an answer to an open question or choice, including REJECT-override rationale.
- `templates/docs/workflow.md`, `templates/docs/tool-reference.md`, the branching and migration guides, and the packaged skill templates describe the model.
- Tests and ruff are clean.

## Design Notes

Captured during planning on 2026-11-20 from developer direction. The developer chose the `canonized`/`noted` naming and campaign/encounter-scoped names over a standalone prefix.

## Open Questions

- Short references and uniqueness: does `cNNN-eNNN-slug` need a per-encounter sequence (for example `cNNN-eNNN-NN-slug`) or a short-ref form, or are slugs enough?
- Storage and archival: should rulings be stored per campaign like encounters, and how do they move when a campaign is archived while rulings are still `recorded`?
- Which campaign statuses accept capture (open only, or paused too)? Can a `completed` campaign being reactivated for review fixes record rulings?
- Prime scope: after a merge, recorded rulings from completed campaigns stay visible on main and new campaign branches until planning triages them. Is that intended pressure, or should prime scope to the active campaign?
- Can one ruling canonize into several lore entries? Should a later ruling be able to supersede an earlier one?
