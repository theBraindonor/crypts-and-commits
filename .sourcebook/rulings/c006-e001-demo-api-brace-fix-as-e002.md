---
archived: false
campaign: c006-applicable-lore-mcp-paging
created_by: John Hoff
created_on: '2026-11-21T17:28:06Z'
encounter: e001-applicable-lore-mcp-paging
history: []
name: c006-e001-demo-api-brace-fix-as-e002
origin: John Hoff (GM), during c006/e001 verification
resolution: null
status: recorded
summary: The pre-existing demo-api bug, where live sourcebook text is passed to ChatPromptTemplate
  unescaped so braces such as c006's `{items, next_cursor}` become template variables
  and 4 chat tests fail, is fixed in a new scripted encounter c006/e002 in the demo-api
  region with its own independent review. It is not an e001 deviation or a rumor.
  e001 stays open until the suite is green.
updated_by: John Hoff
updated_on: '2026-11-21T17:28:06Z'
---

## Decision

Add a scripted encounter c006/e002 in the `demo-api` region to make `demo_api.chat.graph._build_prompt` treat the priming text as a literal system message, so braces in sourcebook content are never parsed as template variables, with a regression test. It goes through its own independent review. c006/e001 stays `open` until the full suite passes, then both are completed.

## Context

During e001's verification, `pdm run pytest -q` failed 4 `demo-api` chat tests with `ChatPromptTemplate is missing variables {'items, next_cursor'}`. `render_context_priming(REPO_ROOT)` includes the active campaign body, and c006's body contains `{items, next_cursor}`. The bug predates c006: any brace in a campaign body, world body or lore/region summary would trigger it. Reverting e001's code would not fix it. The alternatives were fixing it inside e001 (a region its review never covered) or capturing a rumor only (leaving the suite red, contrary to `clean-tests-and-lint`).

## Consequences

- c006 grows to two encounters; b008 is vanquished only once both complete.
- e001's own changes are verified apart from these 4 tests; e002 must turn them green.
