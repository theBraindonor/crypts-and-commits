---
archived: true
campaign: c006-applicable-lore-mcp-paging
created_by: John Hoff
created_on: '2026-11-21T17:22:48Z'
encounter: e001-applicable-lore-mcp-paging
history:
- action: canonize
  by: John Hoff
  message: Canonized into lore cli-mcp-parity with developer approval on planning,
    2026-11-23. The same new paging bullet (shared with c006-e001-json-measured-applicable-lore-paging)
    requires the reserved envelope to include any field the references.inputs decorator
    adds, such as identity, so decorator-added fields can never push a page over budget.
    The exact {items, next_cursor, identity} shape of prime_applicable_lore stays
    documented in tool-reference.md.
  'on': '2026-11-23T18:14:34Z'
name: c006-e001-applicable-lore-keeps-encounter-identity
origin: John Hoff (GM), during c006/e001 implementation
resolution: Canonized into lore cli-mcp-parity with developer approval on planning,
  2026-11-23. The same new paging bullet (shared with c006-e001-json-measured-applicable-lore-paging)
  requires the reserved envelope to include any field the references.inputs decorator
  adds, such as identity, so decorator-added fields can never push a page over budget.
  The exact {items, next_cursor, identity} shape of prime_applicable_lore stays documented
  in tool-reference.md.
status: canonized
summary: 'prime_applicable_lore''s paged MCP result keeps the selected encounter''s
  identity that the shared references.inputs decorator adds to dict results: {items,
  next_cursor, identity}. The paging helper reserves that identity''s compact JSON
  in its envelope, and CLI and MCP pass the same identity, so page breaks stay identical
  and pages fit the budget. There are still no per-item identities.'
updated_by: John Hoff
updated_on: '2026-11-23T18:14:40Z'
---

## Decision

Keep the `identity` field that `references.inputs("encounter")` adds to `prime_applicable_lore`'s new dict result, rather than stripping it. `core/prime.py::page_applicable_lore` takes the selected encounter's identity and counts `{"items": [], "next_cursor": "<n>", "identity": {...}}` as its envelope. Both the MCP wrapper and the CLI pass the same identity, so pages break at the same entries and each MCP result fits the response budget (except a single entry that alone exceeds it). `tool-reference.md` documents `{items, next_cursor, identity}`.

## Context

The reviewed e001 plan specified `{items, next_cursor}`. Implementation showed the decorator adds the encounter identity (about 150 characters) to any dict result, after the page is sized; a test caught a 487-character result against a 400 budget. The old bare-list result never received one. Every other encounter-targeted MCP result carries `identity`, `tool-reference.md`'s Canonical identity section says so, and the CLI already prints the same identity as an `identity:` line. The alternative was to strip it from this one tool.

## Consequences

- MCP consumers get the selected encounter's identity alongside each page.
- b008's "no identities" decision still holds for per-item identities: there is no `identities` array.
- The page budget is slightly smaller, by the identity's size, on both surfaces.
