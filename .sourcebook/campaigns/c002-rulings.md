---
archived: false
bosses:
- b005-ruling-records
created_by: John Hoff
created_on: '2026-11-21T00:32:17Z'
name: c002-rulings
status: open
updated_by: John Hoff
updated_on: '2026-11-21T03:56:19Z'
---

Deliver **rulings** (`b005-ruling-records`): ADR-style records of decisions the developer (GM) confirms during active development. Rulings are captured inside an open campaign and named `cNNN-eNNN-slug`. Each one stays `recorded` until planning gives it a narrative disposition: `canonized` into the world (lore, regions or the world summary and settings), or `noted`. After that it is archived. b005's body is the design reference for every encounter in this campaign. Its design is frozen now that it is assigned, so follow-up ideas became rumors or rulings, not boss edits. Its summary still says "lore"; ruling `c002-e007-canonize-targets-lore-region-world` widens canonizing to lore, region or world.

## Goals

- **Ruling records.** A managed `rulings` collection with an `archive/rulings` counterpart. Each ruling has a required summary (at most 500 characters), a free-text origin and a body, plus a `recorded` / `canonized` / `noted` lifecycle in which both dispositions require a narrative, stored as `resolution`. Only `recorded` rulings are editable. Rulings can be reopened, keep a transition history and can be archived, but cannot be deleted. Archiving a ruling is independent of archiving its campaign.
- **Naming and capture guards.** Every name has the form `cNNN-eNNN-slug`, taken in full; there are no short refs. The campaign must exist and be `open`; reactivation counts, because a reactivated campaign is `open`. A nonzero encounter must exist in that campaign; `e000` marks a campaign-level ruling. Names are unique across live and archived rulings. There are no sequence numbers and no renumber operation.
- **Interfaces.** `ruling_create`, `ruling_get`, `ruling_list` (with `status` and `include_archived` filters), `ruling_update`, `ruling_canonize`, `ruling_note`, `ruling_reopen` and `ruling_archive` MCP tools, with matching `cac ruling` commands, shipped together (`cli-mcp-parity`).
- **Prime and search.** Prime lists every live `recorded` ruling, from any campaign, as summary-only `recorded_rulings` entries within the shared response budget, with an exact `recorded_ruling_count` and `ruling_diagnostics` for damaged records. Rulings have their own `ruling` search type, and an index built before rulings were indexed reports stale once any ruling exists.
- **Skills.** campaign-manager, and any skill working in an open campaign, captures a ruling when the developer confirms an answer to an open question or choice, including the reason for a GM override of a reviewer REJECT. world-planner triages recorded rulings on planning alongside rumors: it canonizes them after making developer-approved lore, region or world changes, or notes them, then archives them. world-manager's prime description and disclosure ladder cover recorded rulings. All three ship in Claude and Codex flavors.
- **Docs.** The workflow guide and tool reference are the authority. The branching guide, migration guide (rulings are additive within schema version 1), this repo's `CLAUDE.md` (`AGENTS.md` imports it and needed no change), `README.md`, the package README, `QUICKSTART.md` and an `[Unreleased]` `CHANGELOG.md` entry describe the model. The world summary and the `crypts-and-commits` region text are updated too.

## Out of scope

- Formal links from a ruling to lore, a region, the world, a superseded ruling, or a boss. Narrative text carries these relationships.
- Automatic ruling capture enforced by core.
- Any change to rumor or boss lifecycles.

## Encounters

Each encounter was drafted, independently reviewed against lore and approved through the normal lifecycle.

1. `e001-ruling-records-core`: core ruling storage, naming and capture guards, and lifecycle, with `ruling` CLI/MCP.
2. `e002-ruling-search-index`: the `ruling` search type and index freshness evidence.
3. `e003-ruling-prime-exposure`: prime exposure of recorded rulings.
4. `e004-ruling-workflow-procedure`: the workflow guide and tool reference.
5. `e005-ruling-skill-templates`: the world-planner, campaign-manager and world-manager skill templates (Claude and Codex), including GM-override capture.
6. `e006-ruling-guides-and-public-docs`: the branching and migration guides, repo `CLAUDE.md`, public docs, and the world and region priming text.
7. `e007-canonize-targets-lore-region-world`: aligned all wording with canonizing into lore, region or world (developer decision after review of the delivered work).

## Rulings recorded during the campaign

- `c002-e001-e000-doc-exemption`
- `c002-e001-workflow-cap-stopgap` (follow-up: rumor `r004-split-workflow-guide-by-phase`)
- `c002-e006-region-text-in-scope`
- `c002-e007-canonize-targets-lore-region-world`

All are left `recorded` for planning triage after integration.

## Completion

The campaign completes when the goals above are implemented and verified, tests and ruff are clean per `clean-tests-and-lint`, skills and docs are consistent, and the campaign is ready for its implementation PR into `main`.

## Log
