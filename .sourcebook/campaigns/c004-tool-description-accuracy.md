---
archived: false
bosses:
- b004-tool-description-accuracy
created_by: John Hoff
created_on: '2026-11-21T05:50:00Z'
name: c004-tool-description-accuracy
status: draft
updated_by: John Hoff
updated_on: '2026-11-21T05:50:00Z'
---

# c004-tool-description-accuracy

## Objective

Vanquish b004-tool-description-accuracy: make the MCP tool descriptions and matching `cac` CLI help that agents actually read accurate, complete, and consistent with `templates/docs/tool-reference.md`, so an agent never has to open the docs to discover a capability a tool already has.

## Selected goals

- **b004-tool-description-accuracy** - success conditions:
  - `index_search` (`mcp/index.py`) and `cac index search` help name every searchable object type and what text each indexes, matching `tool-reference.md`. The current description still says only "Boss summary/body is searchable", although rumors and (since c002) rulings are indexed alongside world, lore, region, campaign and encounter records.
  - Any other description/help drift found is fixed in both surfaces (`cli-mcp-parity`).
  - `pdm run pytest -q` and ruff clean (`clean-tests-and-lint`).

## Tactics

Region: `crypts-and-commits` (`packages/crypts-and-commits`). The work is confined to `mcp/` docstrings, `cli/` help text, the `tool-reference.md` cross-check, and tests. Domain logic in `core/` should not change, except to expose an existing constant if a drift-guard test needs one.

Planned encounters (allocated when drafted):

1. **index_search description**: rewrite the `index_search` MCP description and the `cac index search` help so they enumerate every type in `SEARCH_INDEX_OBJECT_TYPES` and the text indexed for each, reconciled against `tool-reference.md`. Settle b004's open question here: whether a test asserts that the description names each type in the index's type set, to prevent future drift.
2. **Description/help drift sweep**: audit every MCP tool docstring and its CLI counterpart against `tool-reference.md`, giving particular attention to tools added or changed in c001-c003 (boss, rumor, ruling and docs surfaces). Fix drift in both surfaces. Anything outside b004's scope becomes a rumor, not scope creep.

## Out of scope

- New tools or behavior changes (b003-sourcebook-integrity owns adoption and referenced-delete guards).
- Restructuring `tool-reference.md` itself beyond corrections needed for parity.

## Log
