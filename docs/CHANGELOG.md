# Changelog

All notable changes to Crypts and Commits (CAC) are documented in this file.
The format is loosely based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.2.0] - 2026-08-09

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
