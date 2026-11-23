---
archived: false
bosses:
- b009-json-measured-plain-list-paging
created_by: John Hoff
created_on: '2026-11-23T20:59:56Z'
name: c007-plain-list-json-paging
status: open
updated_by: John Hoff
updated_on: '2026-11-23T21:01:25Z'
---

# c007: JSON-measured paging for plain lists

## Objective

Vanquish b009-json-measured-plain-list-paging. Every plain (unnumbered) list page, MCP and CLI, should be sized from the compact JSON the MCP tool actually returns, with its envelope reserved, so MCP pages fit `config.RESPONSE_BUDGET` and both surfaces break at the same items.

## Starting point

- `core/budget.py::paginate(items, cursor, render=str, budget=None)` measures `len(render(item)) + 1` per item against the budget. `lore_list`, `region_list` and `docs_list` (CLI and MCP) call it with the default `str` render and full budget. That ignores JSON quoting/escaping, docs `summary` fields and the `{items, next_cursor}` envelope.
- c006 added `core/prime.py::page_applicable_lore`. It measures each item with `references.encoded` (compact JSON) and reserves the envelope (`items`, worst-case `next_cursor`, optional `identity`) by shrinking the budget. Ruling c006-e001-json-measured-applicable-lore-paging recorded this approach and flagged the plain lists as a follow-up (r008, now b009).

## Tactics

1. **Generalize the helper into `core/budget.py`.** Add one JSON-measured paging function that takes the items, cursor, a per-item JSON projection, and any extra envelope fields. It reserves the compact-JSON envelope with a worst-case `next_cursor` and measures each item as compact JSON. Re-point `page_applicable_lore` at it with no behavior change. Keep it in `core` and keep the CLI/MCP wrappers thin.
2. **Move the three plain lists onto it.** Update `lore_list`, `region_list` and `docs_list` in both `cli/` and `mcp/`, so each surface pages from the same core call and the same item projection that MCP returns.
3. **Inventory the remaining lists.** Answer b009's open question by checking the identity-bearing lists (boss/campaign/encounter/rumor/ruling) and `index_search`: confirm they are already JSON-measured, or bring them under the same helper if the change is small and same-shaped. Anything larger is captured as a rumor, not added to scope.
4. **Docs and contract.** Update `templates/docs/tool-reference.md`'s budget contract so it covers plain lists (and any list changed in step 3), following `workflow-doc-source-of-truth`. Skill templates need changes only if procedure changes, which is not expected.
5. **Tests.** For each list: a boundary test proving the serialized MCP page fits the budget including its envelope, CLI/MCP page-boundary parity, cursor continuation, and the "one oversized item still gets its own page" rule. Run the `prime_applicable_lore` regression tests unchanged.

## Regions

`crypts-and-commits` (lore: `cli-mcp-parity`, `console-best-practices`, `skills-authored-only-in-templates`, `workflow-doc-source-of-truth`), plus world lore `clean-tests-and-lint`.

## Out of scope

- Changing `config.RESPONSE_BUDGET` or the body continuation (`fit_response`) for `get` tools.
- demo-api's own `list_lore` tool, which calls `cac.core` directly and is not paged.

## Log
