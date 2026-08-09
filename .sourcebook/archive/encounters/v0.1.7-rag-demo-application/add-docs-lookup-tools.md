---
archived: true
campaign: v0.1.7-rag-demo-application
created_by: John Hoff
created_on: '2026-08-06T21:56:21Z'
depends_on:
- add-world-region-lore-search-tools
name: add-docs-lookup-tools
regions:
- demo-api
status: completed
updated_by: John Hoff
updated_on: '2026-08-09T14:09:04Z'
---

## Requirements

- The demo-api chat agent must be able to call tools that list and get the packaged reference docs (`workflow`, `migration-guide`) - backed directly by `cac.core.docs`, never a `cac` CLI subprocess or the MCP server (per the `demo-api-uses-cac-core-directly` region lore).
- This closes the RAG-grounding surface the `v0.1.7-rag-demo-application` campaign's acceptance shape explicitly names: grounding via both `index_search` (already shipped as `search_sourcebook` in `add-world-region-lore-search-tools`) and `docs_list`/`docs_get` (this encounter).
- Tools stay strictly read-only: only `cac.core.docs.list_docs`/`read_doc` are exposed; `cac.core.docs` has no mutating functions at all, so there is nothing to accidentally wrap.
- Follows the existing `tools/` package shape unchanged: a new `docs.py` module exporting `build_tools(root) -> list[BaseTool]`, registered in `tools/__init__.py`'s `_BUILDERS` list - no change to any other tool module or to `graph.py`'s wiring.
- Existing chat behavior and all ten already-shipped tools keep working unchanged.

## Rationale

This is the direct follow-up to `add-world-region-lore-search-tools`, and specifically the missing half of what the campaign body calls out by name: "The agent answers questions with RAG grounded in this repository's own indexed sourcebook content (`index_search`) and packaged docs (`docs_list`/`docs_get`)." The prior encounter shipped the `index_search` side; this one ships the `docs_list`/`docs_get` side, completing that explicit acceptance-criteria pairing.

`cac.core.docs` is a small, fixed, packaged registry (`_DOCS: dict[str, DocEntry]`, currently `workflow` and `migration-guide`) - `list_docs()` returns `(name, summary)` pairs and `read_doc(name)` returns a doc's full body, raising `DocNotFoundError` for an unregistered name. Unlike every other `cac.core` module this project's tools have wrapped so far, none of `docs.py`'s functions take a `root: Path` argument at all - the docs are packaged with `cac` itself, not stored in this project's `.sourcebook`. `build_tools(root: Path)` still accepts (and ignores) `root`, purely to keep the same signature as every other module in `_BUILDERS` - the aggregator in `tools/__init__.py` calls every builder uniformly, and special-casing one module to take no argument would complicate that loop for no benefit.

`get_doc` returns both `summary` and `body` (via `read_doc` plus `doc_summary`) rather than body alone, so the chat agent can decide whether a doc is relevant without first fetching its full text - the same "cheap routing signal before the expensive read" shape `prime_applicable_lore` already uses elsewhere in this project.

## Plan

1. Add `packages/demo-api/src/demo_api/chat/tools/docs.py`: `build_tools(root: Path) -> list[BaseTool]` (accepting and ignoring `root`, per Rationale) returning:
   - `list_docs()` - wraps `cac.core.docs.list_docs()`, returns `[{"name": ..., "summary": ...}, ...]`.
   - `get_doc(name: str)` - returns `{"name": name, "summary": cac.core.docs.doc_summary(name), "body": cac.core.docs.read_doc(name)}`; `DocNotFoundError` for an unknown name propagates unchanged, same as every other domain's not-found handling.
2. Update `packages/demo-api/src/demo_api/chat/tools/__init__.py`: add `docs` to the `_BUILDERS` list.
3. Tests, extending `packages/demo-api/tests/test_tools.py`:
   - `list_docs` and `get_doc("workflow")` asserted against `cac.core.docs.list_docs()`/`doc_summary()`/`read_doc()` directly (comparing against the live registry, not hardcoded strings, so the test doesn't drift if a doc's summary text changes).
   - `get_doc("missing")` raises `DocNotFoundError`.
   - Extend `test_build_tools_aggregates_every_domain`'s expected name set to include `list_docs`/`get_doc` (twelve tool names total).

## Verification

- `pdm run pytest packages/demo-api -q` and the full `pdm run pytest -q` both pass.
- `pdm run ruff check .` reports zero errors and `pdm run ruff format .` reports no diffs.
- Manually start the demo-api server and send a `/chat` message asking about the project's workflow/lifecycle rules (e.g. "what are the encounter status transitions?") to confirm a real `get_doc`/`list_docs` round trip; best-effort given this region's noted OpenRouter free-tier rate-limit flakiness, not a hard blocker.

## Log

### Review - 2026-08-06T21:58:33Z - John Hoff

Reviewed against both applicable lore items (clean-tests-and-lint, demo-api-uses-cac-core-directly): the Plan honors both - it calls cac.core.docs functions directly and in-process (never CLI subprocess or MCP), stays strictly read-only (verified cac.core.docs has no mutating functions), and its Verification step matches the pytest/ruff gate exactly. All cited symbols and files were independently verified to exist with the claimed signatures/contents (cac.core.docs's list_docs/doc_summary/read_doc/DocNotFoundError/_DOCS registry, tools/__init__.py's _BUILDERS aggregator, and test_tools.py's existing 10-tool baseline and not-found-error test pattern), and the campaign body was confirmed to literally name both index_search and docs_list/docs_get as the required RAG-grounding pairing. One minor, unchased flag: build_tools(root) in the new module ignores root entirely, unlike every existing sibling tool module - worth a quick ruff sanity check for unused-argument rules during implementation, but not a lore conflict.

### Completed - 2026-08-06T22:25:59Z - John Hoff

Implemented and verified: new demo_api/chat/tools/docs.py wraps cac.core.docs.list_docs/doc_summary/read_doc as list_docs/get_doc LangChain tools, registered in tools/__init__.py's _BUILDERS list. This completes the campaign's explicit RAG-grounding pairing (index_search + docs_list/docs_get) started in add-world-region-lore-search-tools. Extended tests/test_tools.py with coverage comparing tool output against the live cac.core.docs registry (not hardcoded strings) plus a not-found case. Full suite (794 tests) passes, ruff clean - including confirming the reviewer's flagged concern (build_tools(root) ignoring root) doesn't trip any lint rule, since this project's ruff config uses only default rule selection. Live /chat smoke test asked the agent for the exact encounter status transitions per the workflow doc; it returned a precise, accurate table matching the real lifecycle rules, confirming a genuine get_doc round trip.
