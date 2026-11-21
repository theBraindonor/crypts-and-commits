---
archived: false
created_by: John Hoff
created_on: '2026-11-21T16:11:02Z'
depends_on: []
name: b008-applicable-lore-mcp-paging
status: available
summary: 'Give the MCP tool prime_applicable_lore the same cursor paging as cac prime
  applicable-lore (cli-mcp-parity): an optional cursor and a paged {items, next_cursor}
  result (no identities) via budget_core.paginate. Breaking, so bump the pyproject
  versions 0.3.0 -> 0.4.0 (no tag/release; schema stays 1) and give migration-guide
  a 0.4.0 subsection, separate from prior releases. Update tool-reference.md, guides,
  skill templates and tests.'
updated_by: John Hoff
updated_on: '2026-11-21T16:26:42Z'
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
- **Version bump, pyproject files only:** `version` goes from 0.3.0 to 0.4.0 in the root `pyproject.toml`, `packages/crypts-and-commits/pyproject.toml` and `packages/demo-api/pyproject.toml`. Refresh `pdm.lock` only if PDM reports it stale because of the bump. Out of scope: `packages/demo-ui/package.json` and its lock, `docs/CHANGELOG.md`, cutting a release and tagging `v0.4.0`, which the developer will do later. `SOURCEBOOK_SCHEMA_VERSION` stays at 1: no record format changes, and a schema bump would make `cac bootstrap init` report a migration that isn't needed.
- **Migration details segregated by release:** `migration-guide.md`'s "Version-specific migrations" section gains a release-labeled subsection for 0.4.0 (e.g. `### Upgrading from 0.3.0 to 0.4.0`), kept separate from the 0.3.0 Boss Edition notes. It holds b008's note: the result changed from a bare list to `{items, next_cursor}` within schema 1, with no record migration, guardrail suspension or bootstrap migration, and redeploying skills (developer-run `cac bootstrap init`) makes agents follow `next_cursor`. Existing post-0.3.0 migration notes, such as c002's "Rulings are additive within schema version 1" paragraph, move into that 0.4.0 subsection, so the section never mixes notes from different releases. Their content is unchanged.
- `tool-reference.md` documents the new argument and result shape (`workflow-doc-source-of-truth`).
- Every packaged doc and skill template that calls `prime_applicable_lore` is updated, in both the Claude and Codex flavors, including the campaign-manager reviewer prompt (`skills-authored-only-in-templates`). Deployed skill copies are redeployed by the developer.
- MCP and CLI tests cover first page, continuation and invalid cursor. Descriptions stay clean prose and consistent (`cli-mcp-parity` Description accuracy).
- `pdm run pytest -q` and ruff are clean.

## Design Notes

- Expected to fit a single encounter: a small code change plus version, doc and skill template updates.
- Planning decisions, 2026-11-21 (developer):
  - **Result shape:** plain `{items, next_cursor}`, matching the other unnumbered lists (`lore_list`, `region_list`, `docs_list`). Lore names aren't numbered, so `identity_page` identities would carry nothing useful.
  - **Upgrade documentation:** a migration-guide note, following the precedent there for prime's `active_boss` → `active_boss_names` result change, plus the `tool-reference.md` contract update.
  - **Versioning:** bump only the pyproject `version` fields to 0.4.0, because the migration note documents a breaking change and must name its target release. Keep the sourcebook schema at 1. The CHANGELOG, release and tag come later, outside this goal.
  - **Release segregation:** the purpose of the bump is to keep migration details for changes since 0.3.0 clearly apart from prior releases' notes, so the migration guide gets a 0.4.0 subsection and existing post-0.3.0 notes move into it.
- Context: `main` was 55 commits past the `v0.3.0` tag when this was planned, with `pyproject.toml` still at 0.3.0. Post-0.3.0 migration notes (c002 rulings) currently sit unlabeled alongside the Boss Edition notes.

## Open Questions

None.
