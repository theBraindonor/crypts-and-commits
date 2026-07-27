---
campaign: v0.1.2-encounter-indexing-and-search
created_by: John Hoff
created_on: '2026-07-27T05:01:56Z'
depends_on: []
name: add-index-status-search-mcp-tools
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-07-27T05:27:52Z'
---

## Requirements

Add MCP tools mirroring the `cac index status` and `cac index search` CLI commands (`cli/index.py`), per the `cli-mcp-parity` lore: every CLI command needs a matching MCP tool in `mcp/`, except `bootstrap` and (as of the just-updated lore) `index rebuild`, which are permanently developer-only and stay CLI-only. `index status` and `index search` are ordinary read operations and are explicitly *not* covered by that exception, so they must get MCP wrappers.

## Rationale

`core/search_index.py` already implements `index_counts()` (backing `status`) and `search()` (backing `search`) - both pure `core` functions with no CLI-only concerns. Without an MCP wrapper, an agent with only MCP access (no CLI fallback) cannot query the search index at all, defeating the point of having built it. `index rebuild` stays CLI-only by design (developer-triggered maintenance), so this encounter is scoped to the two read commands only.

## Plan

1. Add `packages/crypts-and-commits/src/cac/mcp/index.py`, following the existing thin-wrapper pattern (e.g. `mcp/campaign.py`):
   - `index_status()` -> wraps `search_index_core.index_counts(Path.cwd())`. Returns counts by object type, or an explicit "no index built yet" signal when `None` (mirroring the CLI's message, since there's no console to print to).
   - `index_search(phrase, max_results=..., skip=0, object_type=None, snippet_tokens=...)` -> wraps `search_index_core.search(...)`, using the same defaults as the CLI (`SEARCH_DEFAULT_MAX_RESULTS`, `SEARCH_DEFAULT_SNIPPET_TOKENS`). Let `EmptySearchPhraseError`/`InvalidSearchQueryError` propagate as tool errors rather than adapting them to a CLI-style `fail()` exit. Return structured hits (rank, score, object_type, campaign, name, status, updated_on, excerpt) rather than printed lines, or the "no index built yet" signal when the result is `None`.
   - Do not add an `index rebuild` MCP tool - it stays a permanent CLI-only exception per the updated `cli-mcp-parity` lore.
2. Wire the new module into `mcp/server.py`'s `_TOOL_MODULES`.
3. Update `tests/mcp/test_server.py::test_all_domain_tools_are_registered` to include the new tool set.
4. Add `tests/mcp/test_index.py` covering: no-index-built response for both tools, a populated status count, a search with results, a search with no results, and the invalid-input error paths (empty phrase, bad object_type, out-of-range snippet_tokens).

## Verification

- `pdm run pytest packages/crypts-and-commits/tests/mcp -q` passes, including the new `test_index.py`.
- `pdm run pytest -q` (full suite) passes.
- `pdm run ruff check .` passes.
- Manually exercise both new tools against this repo's own `.sourcebook` (already indexed) via the MCP server to confirm they return sane results.

## Log

### Review - 2026-07-27T05:04:40Z - John Hoff

Reviewed against cli-mcp-parity, clean-tests-and-lint, and console-best-practices. The Plan correctly scopes new MCP tools to `index status`/`index search` only, excludes `index rebuild` per the lore's permanent exception, follows the existing thin-wrapper pattern (mcp/campaign.py), wires into mcp/server.py's _TOOL_MODULES, and updates test_all_domain_tools_are_registered - verified directly against cli/index.py, core/search_index.py, mcp/campaign.py, and mcp/server.py. One gap: the Verification section omits `ruff format .` (no-diff check), which clean-tests-and-lint requires alongside `ruff check .` - add it before treating Verification as satisfied. console-best-practices doesn't apply since no cli/* console output changes. Approved to proceed with that one addition.

### Message - 2026-07-27T05:04:46Z - John Hoff

Per the review note: also run `pdm run ruff format .` (no remaining diff) as part of Verification, alongside `pdm run ruff check .` - required by the clean-tests-and-lint lore, omitted from the original Verification section text.

### Completed - 2026-07-27T05:27:52Z - John Hoff

Verified last session (tests, full suite, ruff check/format, manual smoke test) and re-confirmed this session after restart: index_status and index_search are live MCP tools returning correct results against this repo's own indexed .sourcebook.
