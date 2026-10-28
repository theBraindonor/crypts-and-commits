---
assigned_lore:
- clean-tests-and-lint
name: Crypts and Commits
schema_version: '1'
updated_by: John Hoff
updated_on: '2026-10-28T16:56:44Z'
---

# Crypts and Commits

Crypts and Commits ("CAC") is a Coding Assistant Continuity Framework: a way of structuring collaboration between a developer and an AI coding assistant using a tabletop-gaming metaphor. The developer plays Game Master, establishing context, making judgment calls, and retaining final authority over the session; the assistant plays through that context to get work done. The `crypts-and-commits` MCP server (with the `cac` CLI as its fallback) is the tool an assistant uses to record project context and track its own work across sessions, so continuity survives context resets and session boundaries instead of being rebuilt from scratch each time.

This repository is both the framework's implementation and its first user: as `cac` is built out, this project's own `.sourcebook` is driven through the same MCP/CLI surface, ahead of the longer-term goal of using CAC to drive AI-assisted work on other projects.

## Domain model

- **World** (this record) - project-level summary, read first to prime context. Also holds the `merge_target_branch` and `planning_branch` settings used by the branch workflow.
- **Lore** - standards, conventions, and best practices used to review an encounter before work starts. World-assigned lore is global; region-assigned lore only applies within that region.
- **Region** - a documented path within the repository (e.g. frontend vs. backend) that carries its own conventions and lore.
- **Boss** - a project goal captured and refined before any campaign commits to it: `proposed` -> `available` -> `vanquished` (only by completing its campaign), or `withdrawn`; with graph-validated `depends_on` prerequisites, optional roadmap provenance, and archival.
- **Campaign** - a long-running initiative, analogous to a Jira Epic, expected to span many encounters. Selects zero, one or many bosses while `draft`; `draft` -> `open` <-> `paused` -> `completed` / `abandoned`, at most one open per checkout, and reactivation of a completed campaign for pre-merge review fixes.
- **Rumor** - a standalone backlog note ("we think X should be done") from anywhere, captured on any branch with a summary and free-text origin: `open` -> `promoted` (linked, on the rumor only, to an unassigned boss) or `dismissed`, with reopen and archival but no delete. Triaged on the planning branch, where number collisions are renumbered.
- **Encounter** - a concrete unit of work within a campaign, `scripted` (Requirements, Rationale, Plan, Verification) or `unscripted` (a record of already-done work), carried through `draft` -> `reviewed` (independent lore review) -> `open` -> `completed`, or `abandoned` from any non-completed status.

Bosses, campaigns, encounters and rumors use numbered names (`b001-...`, `c001-...`, `e001-...`, `r001-...`), referenceable by short refs (`bNNN`, `cNNN`, `rNNN`, `cNNN/eNNN`); the skills allocate numbers, core never does.

## Skills and workflow

`world-manager` primes static context, `world-planner` owns goal planning and rumor triage, and `campaign-manager` owns tactical selection and encounter execution. The recommended branch workflow - planning on the planning branch, goal registration on an assignment branch, execution on the campaign's own branch, integration into the merge target - is skill guidance; endpoints stay branch-agnostic. The registered `workflow`, `tool-reference`, `branching-guide` and `migration-guide` docs (`docs_get`) are the detailed references.

## Guardrail

`.sourcebook/` content is managed exclusively through the `crypts-and-commits` MCP tools, falling back to the `cac` CLI only when MCP is unavailable - never by reading or editing files under it directly. `cac bootstrap init` and `cac index rebuild` are run by the developer only - never by the assistant.
