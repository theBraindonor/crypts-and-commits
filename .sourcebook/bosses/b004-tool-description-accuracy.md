---
archived: false
campaign: c004-tool-description-accuracy
created_by: John Hoff
created_on: '2026-11-20T23:43:33Z'
depends_on: []
name: b004-tool-description-accuracy
status: vanquished
summary: Keep MCP tool descriptions and matching CLI help accurate and in parity with
  tool-reference.md, starting with index_search naming every searchable object type
  (including rumor) and what text each indexes.
updated_by: John Hoff
updated_on: '2026-11-21T06:20:55Z'
---

## Goal

Make the MCP tool descriptions and `cac` help text agents actually read accurate, complete and consistent with `templates/docs/tool-reference.md`, so an agent never has to read the docs to discover a capability a tool already has.

## Rationale

The `index_search` description reads "Boss summary/body is searchable. Archives are excluded unless requested." Since e023, rumors are indexed too (type `rumor`: summary, origin and body), along with world, lore, region, campaign and encounter records. An agent reading only the description would not know it can pass `object_type="rumor"` (r003). Descriptions drift as features land; this goal is the home for such fixes.

## Success Criteria

- `index_search` (`mcp/index.py`) and `cac index search` help name every searchable object type and what text each indexes, matching `tool-reference.md`.
- Any other description/help drift found while doing this is fixed in both surfaces (`cli-mcp-parity`).
- Tests and ruff clean.

## Design Notes

Promoted from r003-index-search-description-lists-all-types during planning, 2026-11-20. Intentionally small; future description-accuracy rumors may be promoted to this goal while it is unassigned.

## Open Questions

- Should a test assert that the `index_search` description names each type in the index's type set, to prevent future drift?
