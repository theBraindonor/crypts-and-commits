---
archived: false
created_by: John Hoff
created_on: '2026-10-27T03:26:33Z'
name: c001-boss-edition
status: draft
updated_by: John Hoff
updated_on: '2026-10-27T03:28:46Z'
---

Deliver "Boss Edition", the next CAC release: add **bosses**, project goals that can be captured and refined before any campaign commits to them, plus the numbered-name and branch workflow that ties bosses, campaigns, and encounters together. The full design, including all agreed decisions, lives in `docs/boss-edition.md` (committed on this branch). That doc is the reference for every encounter in this campaign. Where an encounter and the doc disagree, fix the doc in the same change rather than drifting from it.

This is the first numbered campaign. It has no boss, since no boss records exist yet, so per the design it skips the assignment branch and is drafted and executed directly on its execution branch, `c001-boss-edition`. Encounters are numbered `e001`, `e002`, ... in creation order.

## Goals

- **Boss records.** A new managed `bosses` collection with `proposed` / `available` / `withdrawn` / `vanquished` statuses, an `archived` flag (moving the record to `archive/bosses`), `depends_on` prerequisites with graph validation, and `boss_candidates` explaining eligibility and blockers, ordered by boss number.
- **Promotion and coupling.** `boss_assign_campaign` creates a draft campaign linked to a boss. Campaign complete/abandon/reactivate/archive update the linked boss's frontmatter (never its body). Add `campaign_reactivate` (`completed` -> `open`) for PR review fixes.
- **Rumors.** One optional freeform markdown file per campaign under `bosses/rumors/`, with simple CLI/MCP document operations; it can be deleted on planning, never archived.
- **Numbered names and short refs.** Resolve `bNNN`, `cNNN`, and `cNNN/eNNN` short references. Skills allocate numbers; core does not.
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

## Completion

The campaign completes when the features above are implemented and verified, with tests and ruff clean per `clean-tests-and-lint`. The skills and docs must be consistent with each other, and the campaign must be ready for its implementation PR into `main`.
