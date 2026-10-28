# Changelog

All notable changes to Crypts and Commits (CAC) are documented in this file.
The format is loosely based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased] - Boss Edition

Boss Edition adds project goals ("bosses") that can be captured and refined
before any campaign commits to them, plus the numbered-name and branch
workflow that ties bosses, campaigns, and encounters together. Everything
below is the result of the `c001-boss-edition` campaign tracked in this
repository's own `.sourcebook`. The release number has not been chosen yet.
The sourcebook schema stays at version 1: all new storage is additive and
created lazily, with no record migration or bootstrap rerun required.

### Added

- Bosses (`boss_*` / `cac boss`): a managed goal collection with `proposed`,
  `available`, `withdrawn`, and `vanquished` statuses, an `archived` flag,
  graph-validated `depends_on` prerequisites, and design freezing once a goal
  is linked or vanquished.
- Boss candidates (`boss_candidates`), explaining each unassigned goal's
  eligibility and blockers in deterministic boss-number order.
- Roadmap adoption (`boss_record`): incremental recording of existing
  planned, in-progress, or completed goals with immutable provenance,
  including historical completions that satisfy prerequisites without
  synthetic campaigns.
- Campaign boss membership: a campaign selects zero, one, or many bosses,
  via `campaign_create(bosses=...)`, `campaign_set_bosses`, or the
  single-goal `boss_assign_campaign` promotion. Membership locks once the
  campaign opens, and complete/abandon/archive update the linked bosses'
  frontmatter, never their bodies.
- `campaign_reactivate`, reopening an unarchived completed campaign for
  pre-merge review fixes while keeping its closing history.
- Rumors (`rumors_*` / `cac rumors`): one optional freeform document per
  campaign for discoveries made during execution.
- Numbered names and short references: existing-record inputs across the
  CLI and MCP accept `bNNN`, `cNNN`, and `cNNN/eNNN` (exact canonical names
  win); skills allocate numbers, core never does.
- World branch settings `merge_target_branch` and `planning_branch`
  (defaults `main` and `planning`), used by skill branch guidance while
  endpoints stay branch-agnostic.
- Prime and search integration: prime includes the active campaign's
  bosses with integrity diagnostics, bosses are a search object type, and
  the index reports content-based staleness (e.g. after a branch switch)
  instead of returning stale hits.
- Supported continuation reads: every `get` returns `next_cursor` for a
  truncated body and accepts `cursor` / `--cursor` to continue.
- The `world-planner` agent skill (Claude Code and Codex flavors) for goal
  planning, roadmap adoption, readiness assessment, and rumor distillation.
- Packaged docs: the Tool Reference (`tool-reference`), the Branching Guide
  (`branching-guide`), and a Boss Edition upgrade and workflow-adoption
  section in the Migration Guide (`migration-guide`).

### Changed

- Every CLI command that takes `--body` also accepts `--body-file PATH`.
- The packaged Codex `PreToolUse` hook now denies only `apply_patch` edits
  to managed sourcebook paths and no longer filters shell calls.
  `cac bootstrap init` upgrades recognized legacy hook registrations.
- `campaign-manager` and `world-manager` skills were reworked for goal
  selection, numbering, collision checks, and the planning, assignment, and
  execution branch workflow. The Codex `campaign-manager` also gives
  substantive draft and review reports.
- The Workflow Reference Guide (`workflow`) was split into procedure and
  lifecycle rules, with exact tool contracts moved into `tool-reference`.

## [0.2.0] - 2026-08-25

The first public release: `crypts-and-commits` is now installable from PyPI,
and this repository is open to the public. Everything below is the
cumulative result of the `v0.1.0` through `v0.1.7` campaigns tracked in this
repository's own `.sourcebook`, brought to publish-readiness under
`v0.1.8-release-readiness`.

### Added

- The `cac` CLI and `cac-mcp` MCP server, covering the full `.sourcebook`
  domain model: world, lore, region, campaign, and encounter, each with a
  code-enforced status lifecycle where applicable.
- `world-manager` and `campaign-manager` agent skills (Claude Code and Codex
  flavors), deployed into a target project by `cac bootstrap init` and kept
  in sync with the framework's own templates.
- A formal Workflow Reference Guide (`workflow`) documenting the domain
  model's structure and status lifecycles, and a Sourcebook Migration Guide
  (`migration-guide`) for carrying an existing `.sourcebook` forward across
  schema versions — both retrievable on demand via the `docs` MCP/CLI
  surface instead of being pasted into a project's `CLAUDE.md`/`AGENTS.md`.
- Full-text search over `.sourcebook` content (`index_search`/`index_status`),
  incrementally maintained as content changes rather than requiring a manual
  rebuild.
- Archiving for completed/abandoned campaigns and their encounters
  (`campaign_archive`), moving them out of the active working directories
  while keeping them individually readable.
- A demonstration application (`demo-api` + `demo-ui`) showing `cac` used
  by non-`cac` application code in the same repository: a FastAPI backend
  serving a streaming, RAG-grounded chat endpoint over this repository's own
  indexed sourcebook and packaged docs, and a React frontend for it.
- `docs/QUICKSTART.md`, a cold-start setup guide for adopting CAC in another
  project.

### Changed

- `crypts-and-commits` now installs with `pip install crypts-and-commits`;
  the previous git-URL install instructions (needed before this package was
  published) have been retired from `docs/QUICKSTART.md`.
- Package and workspace versions bumped from the placeholder `0.1.0` to
  `0.2.0`, aligning the published version with the `v0.1.x`-campaign-naming
  the project had already moved past.
