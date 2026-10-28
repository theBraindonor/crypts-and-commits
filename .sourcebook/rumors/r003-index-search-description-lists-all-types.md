---
archived: false
boss: null
created_by: John Hoff
created_on: '2026-10-28T17:53:48Z'
history: []
name: r003-index-search-description-lists-all-types
origin: Noticed during c001/e024 execution, 2026-10-28, while searching the sourcebook
  for stale rumor text.
resolution: null
status: open
summary: The index_search MCP tool description only says boss summary/body is searchable;
  it should name every searchable type (including rumors) and what text each indexes.
updated_by: John Hoff
updated_on: '2026-10-28T17:53:48Z'
---

The `index_search` tool description reads: "Boss summary/body is searchable. Archives are excluded unless requested." Since e023, rumors are indexed too, under type `rumor`, covering summary, origin and body. World, lore, region, campaign and encounter records are indexed as well. An agent reading only the tool description would not know it can pass `object_type="rumor"`.

This is a small docstring fix in `mcp/index.py`, possibly also the matching `cac index search` help text. Per `cli-mcp-parity`, both surfaces should say the same thing, and `tool-reference.md` already lists the full coverage.
