---
archived: false
created_by: John Hoff
created_on: '2026-11-21T16:11:02Z'
depends_on: []
name: b008-applicable-lore-mcp-paging
status: proposed
summary: 'Give the MCP tool prime_applicable_lore the same cursor paging as cac prime
  applicable-lore, as cli-mcp-parity requires: an optional cursor argument and a paged
  {items, next_cursor} result built with budget_core.paginate, replacing the bare
  list. Because the result shape changes, update tool-reference.md, the workflow guides
  and skill templates that call it (including the reviewer prompt), and the tests.'
updated_by: John Hoff
updated_on: '2026-11-21T16:11:02Z'
---

## Goal

Bring `prime_applicable_lore` over MCP into line with `cac prime applicable-lore`: both page the applicable-lore set under the response budget with a resumable cursor.

## Rationale

- `mcp/prime.py::prime_applicable_lore(encounter, campaign=None)` returns a bare `list[{name, summary, ref}]` with no `cursor`, while `cli/prime.py::applicable_lore` pages the same `prime_core.applicable_lore` entries with `budget_core.paginate` and `--cursor`.
- `cli-mcp-parity` requires paginated list commands to expose the same cursor paging over MCP, returning structured data. The current gap violates it, and a large applicable-lore set could exceed the response budget over MCP.
- c004/e002 corrected the world-manager skills, which had documented an MCP cursor that doesn't exist. This goal makes that cursor real instead.
- Raised as r005 during c004/e002; promoted during planning on 2026-11-21.

## Success Criteria

- `prime_applicable_lore(encounter, campaign=None, cursor=None)` returns a paged result with `items` (the existing `{name, summary, ref}` entries) and `next_cursor`, using `budget_core.paginate` with the same budget and ordering as the CLI. An invalid cursor raises a clear error.
- The encounter reference contract (`references.inputs("encounter")`) and the campaign default are unchanged.
- `tool-reference.md` documents the new argument and result shape (`workflow-doc-source-of-truth`). Every packaged doc and skill template that calls `prime_applicable_lore` is updated, in both the Claude and Codex flavors, including the campaign-manager reviewer prompt (`skills-authored-only-in-templates`). Deployed skill copies are redeployed by the developer.
- MCP and CLI tests cover first page, continuation and invalid cursor. Descriptions stay clean prose and consistent (`cli-mcp-parity` Description accuracy).
- `pdm run pytest -q` and ruff are clean.

## Design Notes

- This is a breaking change to an MCP result shape (list → object). Agents on older deployed skills would read the new shape after upgrading `cac`; the migration-guide may need a note.
- Expected to fit a single encounter: a small code change plus doc and skill template updates.

## Open Questions

- Should the result also carry identities, as other reference-taking lists do via `identity_page`, or stay `{items, next_cursor}`? Lore names are not numbered, so identities may add nothing.
- Does the migration-guide need an entry for the shape change, or is a CHANGELOG-style note in tool-reference.md enough?
