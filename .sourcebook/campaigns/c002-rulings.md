---
archived: false
bosses:
- b005-ruling-records
created_by: John Hoff
created_on: '2026-11-21T00:32:17Z'
name: c002-rulings
status: draft
updated_by: John Hoff
updated_on: '2026-11-21T00:32:17Z'
---

Deliver **rulings** (`b005-ruling-records`): ADR-style records of decisions the developer (GM) confirms during active development. Rulings are captured inside an open campaign and named `cNNN-eNNN-slug`. Each one stays `recorded` until planning gives it a narrative disposition: `canonized` into the world's lore, or `noted`. After that it is archived. b005's body is the design reference for every encounter in this campaign. Its design is frozen now that it is assigned, so any follow-up idea becomes a rumor, not a boss edit.

## Goals

- **Ruling records.** A new managed `rulings` collection with an `archive/rulings` counterpart. Each ruling has a required summary, a free-text origin and a body, plus a `recorded` / `canonized` / `noted` lifecycle in which both dispositions require a narrative. Rulings can be reopened, keep a transition history and can be archived, but cannot be deleted. Archiving a ruling is independent of archiving its campaign.
- **Naming and capture guards.** Every name has the form `cNNN-eNNN-slug`. The campaign must exist and be `open`; reactivation counts, because a reactivated campaign is `open`. The encounter must exist in that campaign, or be `e000` for a campaign-level ruling. Names are unique across live and archived rulings. There are no sequence numbers and no renumber operation.
- **Interfaces.** `ruling_*` MCP tools and `cac ruling` commands, shipped together in each encounter that introduces them (`cli-mcp-parity`).
- **Prime and search.** Prime includes every `recorded` ruling, from any campaign, within the shared response budget. Rulings also get their own `ruling` search type.
- **Skills and docs.** world-planner triages rulings alongside rumors, and its canonize procedure creates or updates lore with developer approval. campaign-manager, and any skill working in an open campaign, captures a ruling when the developer confirms an answer to an open question or choice, including the reason for a REJECT override. The changes land in the workflow guide, tool reference, branching guide and migration guide, the packaged Claude and Codex skill templates, and this repo's `CLAUDE.md`/`AGENTS.md` domain model.

## Out of scope

- Formal links from a ruling to lore, a superseded ruling, or a boss. Narrative text carries these relationships.
- Automatic ruling capture enforced by core.
- Any change to rumor or boss lifecycles.

## Tentative encounter order

Not a commitment. Each encounter is drafted, reviewed and approved through the normal lifecycle, and each one ships its CLI and MCP surfaces together.

1. Core ruling storage, naming and capture guards, and lifecycle, with `ruling` CLI/MCP.
2. Search index integration (`ruling` type) and index freshness evidence.
3. Prime exposure of recorded rulings.
4. Workflow guide and tool reference.
5. world-planner and campaign-manager skill templates (Claude and Codex).
6. Branching and migration guides, repo `CLAUDE.md`/`AGENTS.md`, and public docs.

## Completion

The campaign completes when the goals above are implemented and verified, tests and ruff are clean per `clean-tests-and-lint`, skills and docs are consistent, and the campaign is ready for its implementation PR into `main`.

## Log
