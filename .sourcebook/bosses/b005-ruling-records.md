---
archived: false
created_by: John Hoff
created_on: '2026-11-21T00:04:48Z'
depends_on: []
name: b005-ruling-records
status: proposed
summary: 'Add rulings: ADR-style records of developer (GM)-confirmed decisions made
  in an open campaign, named cNNN-eNNN-slug (e000 for campaign-level). Archived independently
  of campaigns, like rumors. Prime shows every recorded ruling. Planning gives each
  one a narrative disposition with hindsight: canonized (how the lore was updated)
  or noted (why it needs no lore), then archives it.'
updated_by: John Hoff
updated_on: '2026-11-21T00:12:47Z'
---

## Goal

Give the decisions made during development an identity and a lifecycle, so that planning can review them with hindsight and decide which ones become standing lore. A rumor captures what we might do; a ruling captures what the developer (Game Master) decided while doing it.

## Rationale

Coding assistants working on CAC-driven projects keep recommending architecture decision records (ADRs). Today, developer decisions are scattered across encounter messages, boss design notes, rumor resolutions and GM-override logs, with no way to find them again or to promote them into lore. Whether a decision matters beyond its moment is often unknowable when it is made; the important ones only become clear in hindsight. Rumors already prove the pattern of capturing freely during work and dispositioning deliberately during planning. Lore remains the authority enforced by reviews; rulings become its intake and audit trail.

## Scope and model

- **Rulings belong to active development.** A ruling can only be captured within an `open` campaign. Reactivating a completed campaign for review fixes returns it to `open`, so reactivated campaigns can record rulings. `draft`, `paused` and terminal campaigns cannot, because no work is happening in them. Outside an open campaign there is no ruling; the right capture is a rumor.
- **Naming.** `cNNN-eNNN-slug`, named for the campaign and encounter in which the decision was made, using `e000` for a campaign-level decision with no encounter. Encounters are expected to produce several rulings, so the slug distinguishes them. The name must be unique across all live and archived rulings, and there is no per-encounter sequence number. Campaign numbers are already settled at assignment, so cross-branch collisions are not expected and no renumber operation is needed.
- **Capture trigger.** A ruling records an answer to an open question or choice (a boss's open question, an encounter's open question, a plan choice, or the reason for overriding a reviewer REJECT) that the developer confirmed. Capture is skill guidance that relies on the way agents already ask and resolve open questions with the developer; it is not a rule enforced by core.
- **Content.** A required summary, a free-text origin, and a body recording the decision, its context and its consequences. A later ruling may supersede an earlier one, and says so in its own narrative; no formal supersession link is needed.
- **Lifecycle.** New rulings are `recorded` (untriaged). Planning then marks each one:
  - `canonized`, with a required narrative describing how the world (lore, regions, world summary) was updated to reflect it.
  - `noted`, with a required narrative explaining why it needs no lore.
  
  One ruling may be canonized into any number of lore changes. There are no formal ruling-to-lore links; the narrative is the record. Rulings can be reopened, keep a transition history, and cannot be deleted.
- **Archival.** Rulings are archived independently of campaigns, like rumors. Planning handles them, and archiving a campaign neither moves nor blocks them.
- **Prime.** Prime includes every `recorded` ruling, including rulings from completed campaigns that are still untriaged. That is deliberate: an untriaged decision is worth knowing about, and proper planning clears them. Canonized rulings live on through lore, and noted rulings can be ignored.
- **Planning.** A well-run planning session gives every integrated recorded ruling a disposition, in the same way rumors are promoted or dismissed. If the ruling is canonized, the lore and world changes are made with developer approval and the ruling records how. Every ruling, canonized or noted, is then archived.

## Success Criteria

- Ruling records with the naming, content and lifecycle above. They are created only within an `open` campaign, and only within an existing encounter of that campaign unless `e000` is used. Names are unique across live and archived rulings.
- Full `ruling_*` MCP tools and matching `cac ruling` commands (`cli-mcp-parity`), a `ruling` search type, and prime exposure of all recorded rulings.
- world-planner triages rulings alongside rumors, including the procedure for canonizing a ruling into lore. campaign-manager, and any skill working in an open campaign, captures a ruling when the developer confirms an answer to an open question or choice, including the reason for a REJECT override.
- `templates/docs/workflow.md`, `templates/docs/tool-reference.md`, the branching and migration guides, and the packaged skill templates describe the model.
- Tests and ruff are clean.

## Design Notes

Captured and refined during planning on 2026-11-20 from developer direction. The developer chose:
- `canonized`/`noted` naming;
- campaign/encounter-scoped names with unique slugs, rather than a standalone prefix or sequence numbers;
- open-only capture;
- archival independent of campaigns;
- prime visibility of every recorded ruling;
- narrative dispositions instead of formal lore links.

## Open Questions

None at this time.
