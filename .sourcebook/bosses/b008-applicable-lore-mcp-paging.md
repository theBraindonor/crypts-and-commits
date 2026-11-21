---
archived: false
created_by: John Hoff
created_on: '2026-11-21T16:11:02Z'
depends_on: []
name: b008-applicable-lore-mcp-paging
status: proposed
summary: 'Give the MCP tool prime_applicable_lore the same cursor paging as cac prime
  applicable-lore, as cli-mcp-parity requires: an optional cursor argument and a paged
  {items, next_cursor} result (no identities, like lore_list) built with budget_core.paginate,
  replacing the bare list. Update tool-reference.md, a migration-guide note, the workflow
  guides and skill templates that call it (including the reviewer prompt), and the
  tests.'
updated_by: John Hoff
updated_on: '2026-11-21T16:12:30Z'
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
- `tool-reference.md` documents the new argument and result shape (`workflow-doc-source-of-truth`).
- `migration-guide.md`'s "Version-specific migrations" section gains a short paragraph: the result changed from a bare list to `{items, next_cursor}` within schema 1, with no record migration, guardrail suspension or bootstrap migration; redeploying skills (developer-run `cac bootstrap init`) makes agents follow `next_cursor`.
- Every packaged doc and skill template that calls `prime_applicable_lore` is updated, in both the Claude and Codex flavors, including the campaign-manager reviewer prompt (`skills-authored-only-in-templates`). Deployed skill copies are redeployed by the developer.
- MCP and CLI tests cover first page, continuation and invalid cursor. Descriptions stay clean prose and consistent (`cli-mcp-parity` Description accuracy).
- `pdm run pytest -q` and ruff are clean.

## Design Notes

- Expected to fit a single encounter: a small code change plus doc and skill template updates.
- Planning decisions, 2026-11-21 (developer):
  - **Result shape:** plain `{items, next_cursor}`, matching the other unnumbered lists (`lore_list`, `region_list`, `docs_list`). Lore names aren't numbered, so `identity_page` identities would carry nothing useful.
  - **Upgrade documentation:** a migration-guide note, following the precedent there for prime's `active_boss` → `active_boss_names` result change, plus the `tool-reference.md` contract update.

## Open Questions

None.
