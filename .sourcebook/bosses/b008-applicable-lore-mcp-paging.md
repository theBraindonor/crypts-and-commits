---
archived: false
created_by: John Hoff
created_on: '2026-11-21T16:11:02Z'
depends_on: []
name: b008-applicable-lore-mcp-paging
status: proposed
summary: 'Give the MCP tool prime_applicable_lore the same cursor paging as cac prime
  applicable-lore (cli-mcp-parity): an optional cursor and a paged {items, next_cursor}
  result (no identities) via budget_core.paginate, replacing the bare list. Breaking,
  so bump the package version 0.3.0 -> 0.4.0 (schema stays 1), add a migration-guide
  note naming 0.4.0, a CHANGELOG entry, and update tool-reference.md, guides, skill
  templates and tests.'
updated_by: John Hoff
updated_on: '2026-11-21T16:16:33Z'
---

## Goal

Bring `prime_applicable_lore` over MCP into line with `cac prime applicable-lore`: both page the applicable-lore set under the response budget with a resumable cursor.

## Rationale

- `mcp/prime.py::prime_applicable_lore(encounter, campaign=None)` returns a bare `list[{name, summary, ref}]` with no `cursor`, while `cli/prime.py::applicable_lore` pages the same `prime_core.applicable_lore` entries with `budget_core.paginate` and `--cursor`.
- `cli-mcp-parity` requires paginated list commands to expose the same cursor paging over MCP, returning structured data. The current gap violates it, and a large applicable-lore set could exceed the response budget over MCP.
- c004/e002 corrected the world-manager skills, which had documented an MCP cursor that doesn't exist. This goal makes that cursor real instead.
- Raised as r005 during c004/e002; promoted during planning on 2026-11-21.

## Success Criteria

- `prime_applicable_lore(encounter, campaign=None, cursor=None)` returns `{"items": [...], "next_cursor": ...}`, where `items` are the existing `{name, summary, ref}` entries, paged with `budget_core.paginate` using the same budget and ordering as the CLI. There is no `identities` array. An invalid cursor raises a clear error.
- The encounter reference contract (`references.inputs("encounter")`) and the campaign default are unchanged.
- **Version bump:** the package version goes from 0.3.0 to 0.4.0, a pre-1.0 minor bump for the breaking MCP result change, as part of this goal's work. The workspace keeps its versions in lockstep, so every field that currently reads 0.3.0 moves together: root `pyproject.toml`, `packages/crypts-and-commits/pyproject.toml`, `packages/demo-api/pyproject.toml`, `packages/demo-ui/package.json` and its `package-lock.json`, and `pdm.lock`, regenerated rather than hand-edited. `SOURCEBOOK_SCHEMA_VERSION` stays at 1: no record format changes, and a schema bump would make `cac bootstrap init` report a migration that isn't needed.
- `tool-reference.md` documents the new argument and result shape (`workflow-doc-source-of-truth`).
- `migration-guide.md`'s "Version-specific migrations" section gains a short paragraph naming 0.4.0 as the target release. It says the result changed from a bare list to `{items, next_cursor}` within schema 1, with no record migration, guardrail suspension or bootstrap migration, and that redeploying skills (developer-run `cac bootstrap init`) makes agents follow `next_cursor`.
- `docs/CHANGELOG.md` records the change as a breaking change.
- Every packaged doc and skill template that calls `prime_applicable_lore` is updated, in both the Claude and Codex flavors, including the campaign-manager reviewer prompt (`skills-authored-only-in-templates`). Deployed skill copies are redeployed by the developer.
- MCP and CLI tests cover first page, continuation and invalid cursor. Descriptions stay clean prose and consistent (`cli-mcp-parity` Description accuracy).
- `pdm run pytest -q` and ruff are clean.

## Design Notes

- Expected to fit a single encounter: a small code change plus version, doc and skill template updates.
- Planning decisions, 2026-11-21 (developer):
  - **Result shape:** plain `{items, next_cursor}`, matching the other unnumbered lists (`lore_list`, `region_list`, `docs_list`). Lore names aren't numbered, so `identity_page` identities would carry nothing useful.
  - **Upgrade documentation:** a migration-guide note, following the precedent there for prime's `active_boss` → `active_boss_names` result change, plus the `tool-reference.md` contract update.
  - **Versioning:** bump the package to 0.4.0 in this goal because the migration note documents a breaking change and must name its target release; keep the sourcebook schema at 1.
- Context: `main` was 55 commits past the `v0.3.0` tag when this was planned, with `pyproject.toml` still at 0.3.0 and c002's rulings under CHANGELOG `[Unreleased]`. Changes from c003–c005 aren't in the CHANGELOG yet.

## Open Questions

- CHANGELOG: should b008 cut the `[Unreleased]` section as `[0.4.0]` (dated, folding in c002–c005 and b008), or add its entry under `[Unreleased]` and leave cutting the release, and tagging `v0.4.0`, to a separate release step?
