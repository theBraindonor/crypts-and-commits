---
archived: false
bosses:
- b001-boss-records
- b002-rumor-records
created_by: John Hoff
created_on: '2026-10-27T03:26:33Z'
name: c001-boss-edition
status: completed
updated_by: John Hoff
updated_on: '2026-10-28T22:42:24Z'
---

Deliver "Boss Edition", the next CAC release: add **bosses**, project goals that can be captured and refined before any campaign commits to them, plus the numbered-name and branch workflow that ties bosses, campaigns, and encounters together. The full design, including all agreed decisions, lives in `docs/boss-edition.md` (committed on this branch). That doc is the reference for every encounter in this campaign. Where an encounter and the doc disagree, fix the doc in the same change rather than drifting from it.

This is the first numbered campaign. It has no boss, since no boss records exist yet, so per the design it skips the assignment branch and is drafted and executed directly on its execution branch, `c001-boss-edition`. Encounters are numbered `e001`, `e002`, ... in creation order.

## Goals

- **Boss records.** A new managed `bosses` collection with `proposed` / `available` / `withdrawn` / `vanquished` statuses, an `archived` flag (moving the record to `archive/bosses`), `depends_on` prerequisites with graph validation, and `boss_candidates` explaining eligibility and blockers, ordered by boss number.
- **Promotion and coupling.** `boss_assign_campaign` creates a draft campaign linked to a boss. Campaign complete/abandon/reactivate/archive update the linked boss's frontmatter (never its body). Add `campaign_reactivate` (`completed` -> `open`) for PR review fixes.
- **Rumors.** Standalone, numbered backlog records (`rNNN-slug`, under `.sourcebook/rumors/`, archived under `archive/rumors/`): "we think X should be done" notes with a free-text origin, captured from anywhere and on any branch. Lifecycle `open` -> `promoted` (linked, on the rumor only, to an unassigned proposed/available boss; many rumors may share a boss) or `dismissed` (with a reason), `reopen`, and `archive`; no delete and no dedupe. Number collisions are resolved on the planning branch with `rumor_renumber`, which works on open and dismissed rumors but not on promoted ones. Rumors have their own search type and stay out of prime. (Revised during e023 drafting; replaces the e011 per-campaign rumors document, which was never released.)
- **Numbered names and short refs.** Resolve `bNNN`, `cNNN`, `cNNN/eNNN` and `rNNN` short references. Skills allocate numbers; core does not.
- **Branch workflow as skill guidance.** `merge_target_branch` and `planning_branch` world settings. Endpoints stay branch-agnostic, and the skills carry the planning / assignment / execution branch rules and collision checks.
- **Skills and docs.** A new planning skill (working name `world-planner`), campaign-manager updates, the canonical workflow reference, a new `branching-guide.md`, and migration-guide guidance for adopting projects (including targeted `CLAUDE.md` / `AGENTS.md` updates).
- **Quality-of-life.** CLI `--body-file` for every `--body` command, and a narrower packaged Codex hook that denies only `apply_patch` edits to managed content.
- **Prime and search.** Prime includes the active campaign's boss. Bosses get their own search object type, and the index is handled across branch switches.

## Out of scope

Agent runtimes, messaging, distributed claims, CI enforcement, multi-planner coordination, and branch-dependent endpoint behavior (see the doc's "Scope and boundaries").

## Tentative encounter order

Not a commitment. Each encounter is drafted, reviewed, and approved through the normal lifecycle. Per `cli-mcp-parity`, every encounter that adds or changes a core operation ships its CLI command and MCP tool in the same change; interfaces are never deferred to a separate encounter.

1. Commit the design doc and record the decisions still open (see the doc's "Remaining implementation details"), resolving any needed before core work.
2. CLI `--body-file` support (independent).
3. Narrower Codex hook (independent).
4. World branch settings (`merge_target_branch`, `planning_branch`), with world CLI/MCP exposure.
5. Boss core storage, lifecycle, and dependency validation, with `boss` CLI/MCP commands.
6. Boss candidates and eligibility explanations, with `boss_candidates` CLI/MCP.
7. Short-reference resolution across existing and new CLI/MCP inputs.
8. Promotion (`boss_assign_campaign`), campaign boss link, and coupled campaign lifecycle updates, including `campaign_reactivate`, with CLI/MCP.
9. Rumors documents, with CLI/MCP document operations.
10. Prime and search integration (including stale-index handling across branch switches).
11. Planning skill, campaign-manager updates, and workflow reference.
12. Branching guide and migration guide.
13. Adopt the new workflow in this repo's own `CLAUDE.md` / `AGENTS.md` and sourcebook.
14. Replace item 9's per-campaign rumors documents with standalone `rNNN` rumor records: core/CLI/MCP and owning docs, then skills and guides, then public docs.

## Completion

The campaign completes when the features above are implemented and verified, with tests and ruff clean per `clean-tests-and-lint`. The skills and docs must be consistent with each other, and the campaign must be ready for its implementation PR into `main`.

## Log

### GM override - 2026-10-28 - John Hoff

c001 opened bossless, before any boss records existed. On 2026-10-28 the developer, acting as Game Master, deliberately side-stepped the draft-only membership rule and linked this open campaign to `b001-boss-records` and `b002-rumor-records` by hand-editing their reciprocal frontmatter (`bosses` here, `campaign` on each boss). The goal is that completing c001 vanquishes both through the normal coupled lifecycle. The bosses were created through MCP on this execution branch as a first-adoption exception, because no planning branch exists yet. The link was verified through `prime_get`, `boss_candidates` and `index_status` after a developer index rebuild. The full record, rationale and independent review are in encounter `c001/e025-record-gm-override-linking-c001-bosses`. Rumor `r001-open-campaign-adopts-goals` captures the supported operation that would make this override unnecessary.

### Completed - 2026-10-28T22:42:24Z - John Hoff

c001 delivered Boss Edition across 26 encounters (e001–e026). Shipped: boss records with a proposed/available/withdrawn/vanquished lifecycle, archival, prerequisites checked for cycles, `boss_candidates`, and roadmap adoption with a fixed provenance snapshot (`boss_record`). Numbered names with short-ref resolution, where exact canonical names win. Promotion of bosses into campaigns, multiple bosses per campaign, and campaign complete/abandon/reactivate/archive updating the linked bosses. Standalone rumors that replace the unreleased per-campaign rumors document from e011. Active bosses in prime, plus their own search types. World branch settings, CLI `--body-file`, the narrower Codex `apply_patch` hook, the world-planner skill and campaign-manager updates, and the reworked workflow guide, tool reference, branching guide and migration guide. This repo has adopted the new workflow. What worked: the independent review gate caught real problems, and e017/e018 fixed them before release. What didn't go to plan: the rumor design was revised partway through (e023), which meant a second round of docs alignment (e024, e026). c001 also opened before any bosses existed, so linking b001 and b002 took a GM override (recorded in e025). Follow-ups are captured as r001–r003. Verified: 1,601 tests pass, ruff check and format are clean, no numbering or ownership collisions, and the index is fresh.
