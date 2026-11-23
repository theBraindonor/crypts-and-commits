---
archived: false
created_by: John Hoff
created_on: '2026-11-23T18:37:48Z'
depends_on: []
name: b009-json-measured-plain-list-paging
status: available
summary: 'Give the plain MCP lists (lore_list, region_list, docs_list) the same JSON-measured
  paging prime_applicable_lore got in c006: measure each item as the compact JSON
  actually returned and reserve the result envelope, by generalizing the shared core
  helper rather than adding one per list. MCP pages must fit the response budget and
  break where the CLI''s do; tool-reference''s budget contract is updated to match.'
updated_by: John Hoff
updated_on: '2026-11-23T18:41:19Z'
---

## Goal

Make every plain (unnumbered) MCP list page fit the response budget it is measured against, by sizing pages from the compact JSON the tool actually returns instead of a looser rendering.

## Rationale

Ruling c006-e001-json-measured-applicable-lore-paging moved `prime_applicable_lore` / `cac prime applicable-lore` onto one core helper that measures each item as compact JSON and reserves the result envelope, so MCP pages fit the budget and break at the same places as the CLI. The same ruling noted that `lore_list`, `region_list` and `docs_list` still measure a looser rendering, so an MCP page could exceed the budget. With the `cli-mcp-parity` paging rule canonized from c006's rulings, these lists now fall short of a stated region standard. Raised as r008-json-measure-plain-list-paging.

## Success Criteria

- `lore_list`, `region_list` and `docs_list` (MCP and CLI) page via one generalized core helper derived from the applicable-lore helper — not one helper per list.
- Each MCP page, serialized as the compact JSON returned, fits `config.RESPONSE_BUDGET` including its envelope (`items`, `next_cursor`, any other fields); CLI and MCP page boundaries match.
- `prime_applicable_lore` keeps its current behavior on the generalized helper (no regression).
- `templates/docs/tool-reference.md`'s budget contract covers plain lists, per `workflow-doc-source-of-truth`.
- Tests prove budget fit at the boundary for each list and CLI/MCP boundary parity; `pdm run pytest -q` and ruff are clean.

## Design Notes

Captured from r008 during planning, 2026-11-23, at the developer's choice of a new goal over folding into b003 or dismissal.

## Open Questions

- Are any other list endpoints (e.g. rumor/ruling/boss/campaign lists with identities) still measured loosely, and should they join this goal or be confirmed already compliant?
