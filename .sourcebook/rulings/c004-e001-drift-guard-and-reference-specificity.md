---
archived: false
campaign: c004-tool-description-accuracy
created_by: John Hoff
created_on: '2026-11-21T05:57:29Z'
encounter: e001-index-search-description
history: []
name: c004-e001-drift-guard-and-reference-specificity
origin: Developer (GM), approving c004/e001 review notes before opening
resolution: null
status: recorded
summary: 'Answer b004''s open question with a drift-guard test: it asserts that index_search''s
  MCP description and cac index search help name every SEARCH_INDEX_OBJECT_TYPES value
  (names only, not per-type indexed text). Also add the world/lore/region/campaign/encounter
  "body" clause to tool-reference.md so the owning doc is at least as specific as
  the descriptions it governs.'
updated_by: John Hoff
updated_on: '2026-11-21T05:57:29Z'
---

## Decision

1. b004's open question ("Should a test assert that the index_search description names each type in the index's type set?") is answered **yes**. Two drift-guard tests, one for the MCP `index_search` docstring and one for the `cac index search --help` output, assert that every `SEARCH_INDEX_OBJECT_TYPES` value is named. They cover type names only, not the per-type indexed-text statements; that limit is accepted.
2. Following review note 1, `tool-reference.md`'s Search index section gains the clause that world, lore, region, campaign and encounter records index their body. The owning contract doc should be at least as specific as the agent-facing descriptions it governs. This deviates from e001 Plan step 4's "change only if a factual mismatch is found".

## Context

The independent review of c004/e001 (PASS-WITH-NOTES) noted that the new descriptions would state per-type indexed text that tool-reference.md stated only for boss, rumor and ruling, and that the drift guard checks names only. The developer approved opening e001 with the tool-reference clause included.

## Consequences

- A type added to the index without updating both descriptions fails the suite.
- A change to what an existing type indexes is not caught by the guard; it relies on review, and on tool-reference.md remaining the contract owner.
