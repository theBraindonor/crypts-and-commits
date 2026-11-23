---
archived: false
boss: null
created_by: John Hoff
created_on: '2026-11-23T18:13:12Z'
history: []
name: r008-json-measure-plain-list-paging
origin: Consequence noted in ruling c006-e001-json-measured-applicable-lore-paging;
  captured during c006 ruling triage on planning, 2026-11-23, at the developer's request
resolution: null
status: open
summary: The plain MCP lists (lore_list, region_list, docs_list) still size pages
  by a looser rendering than the compact JSON they return, so an MCP page could exceed
  the response budget. prime_applicable_lore now measures items as compact JSON and
  reserves its envelope via a shared core helper. Consider aligning the other plain
  lists with the same approach.
updated_by: John Hoff
updated_on: '2026-11-23T18:13:12Z'
---

## Observation

Ruling c006-e001-json-measured-applicable-lore-paging switched `prime_applicable_lore` and `cac prime applicable-lore` to one core helper. It measures each item as compact JSON and reserves the result envelope, so MCP pages fit the response budget and break where the CLI's do. The same ruling noted that the other plain (unnumbered) lists, `lore_list`, `region_list` and `docs_list`, still measure a looser rendering. The tool-reference compact-JSON wording strictly covers `get` responses and identity-bearing lists, but the risk of a page running over is the same.

## Suggested action

Plan a goal to give the plain lists the same JSON-measured paging, preferably by generalizing the applicable-lore helper rather than adding one helper per list. Update `tool-reference.md`'s budget contract to match. With cli-mcp-parity's paging rule (canonized from c006's rulings) in place, the current lists would fall short of it.
