---
campaign: v0.1.2-encounter-indexing-and-search
created_by: John Hoff
created_on: '2026-07-27T04:29:16Z'
depends_on: []
name: add-snippet-size-cli-option
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-07-27T04:45:13Z'
---

## Requirements

- Expose the FTS5 `snippet()` token count - currently the hardcoded `_SNIPPET_TOKENS = 12` module constant in `core/search_index.py` - as a `cac index search` CLI option, rather than a fixed value.
- Default value changes from `12` to **`20`** tokens.
- `core/search_index.py`'s `search()` function should accept the token count as a parameter (rather than reading the module constant directly), so `cli/index.py` can pass the CLI option's value through.
- SQLite's `snippet()` caps this value at 64 tokens - decide during implementation whether to clamp, reject, or pass through an out-of-range value.

## Rationale

The excerpt is the main thing a caller reads to judge relevance before opening a hit, and 12 tokens is thin - especially now that world/lore/region bodies (added earlier in this campaign) are indexed alongside encounters and tend to run longer and denser than encounter sections. Raising the default to 20 gives more usable context per hit without a CLI option; making it a per-search option lets a caller trade excerpt length for result density (e.g. shorter snippets to scan more hits per page, longer ones to judge relevance without opening the file) instead of picking one fixed value for everyone.

Decided (via user confirmation while drafting this encounter): out-of-range values are **rejected**, not clamped or passed through to SQLite. This matches the existing `limit`/`offset` validation already in `search()` (`InvalidSearchQueryError` for `limit < 1` or `offset < 0`), keeping all of `search()`'s input validation in one consistent style, and avoids SQLite's own undocumented behavior on an out-of-range `snippet()` token count (a raw `sqlite3.OperationalError` or silently-wrong output) ever reaching a CLI user.

## Plan

1. In `core/config.py`, add `SEARCH_DEFAULT_SNIPPET_TOKENS = 20`, `SEARCH_MIN_SNIPPET_TOKENS = 1`, and `SEARCH_MAX_SNIPPET_TOKENS = 64`, alongside the existing `SEARCH_DEFAULT_MAX_RESULTS` constant.
2. In `core/search_index.py`:
   - Remove the module-level `_SNIPPET_TOKENS = 12` constant.
   - Add a `snippet_tokens: int = SEARCH_DEFAULT_SNIPPET_TOKENS` keyword parameter to `search()`.
   - Validate it alongside the existing `limit`/`offset` checks: raise `InvalidSearchQueryError` if `snippet_tokens` is outside `[SEARCH_MIN_SNIPPET_TOKENS, SEARCH_MAX_SNIPPET_TOKENS]`, with a message stating the valid range.
   - Use the `snippet_tokens` parameter (not the removed constant) in the `snippet(...)` clause of the SQL built in `search()`.
3. In `cli/index.py`'s `search` command, add a `snippet_tokens: int = typer.Option(search_index_core.SEARCH_DEFAULT_SNIPPET_TOKENS, "--snippet-tokens", help="Snippet excerpt length, in tokens (1-64).")` option and pass it through to `search_index_core.search(...)`. Let the existing `except (EmptySearchPhraseError, InvalidSearchQueryError)` block handle the new out-of-range case the same way it already handles bad `limit`/`offset`/`object_type` - no separate error handling needed.
4. Update `tests/core/test_search_index.py`: cover the new default (20), an explicit `snippet_tokens` value changing the returned excerpt, and `InvalidSearchQueryError` for values below 1 and above 64.
5. Update `tests/cli/test_index.py`: cover `--snippet-tokens` being passed through on a successful search, and a non-zero exit with an error message for an out-of-range value.
6. No MCP-side change - `cac index search` has no MCP tool counterpart yet (search is CLI-only for now), so `mcp/` is untouched.

## Verification

- `pdm run pytest -q` passes, with no skips or deletions used to dodge a failure.
- `pdm run ruff check .` reports zero errors and `pdm run ruff format .` reports no diffs.

## Log

### Review - 2026-07-27T04:41:26Z - John Hoff

GM OVERRIDE of independent reviewer REJECT. Reviewer's finding: the Plan modifies cli/index.py's `search` command (adding --snippet-tokens) but declines to add a matching MCP tool, citing only that `cac index search` "has no MCP tool counterpart yet (... for now)" - judged a temporal excuse rather than the permanent, structural exception (like `bootstrap`) the cli-mcp-parity lore requires before skipping parity on a changed CLI command. clean-tests-and-lint and console-best-practices were both judged satisfied. GM reasoning for proceeding as drafted: the pre-existing MCP gap for `cac index search` (status/rebuild/search) is a known, deliberate, already-accepted tradeoff from when index/search was first built CLI-only earlier in this campaign - not a new gap introduced by this encounter, which only adds one parameter to an already CLI-only command. The GM is treating closing that pre-existing gap as out of scope for this encounter and explicitly overriding the REJECT to proceed without MCP parity here.

### Completed - 2026-07-27T04:45:13Z - John Hoff

Implemented as planned: SEARCH_DEFAULT_SNIPPET_TOKENS/SEARCH_MIN_SNIPPET_TOKENS/SEARCH_MAX_SNIPPET_TOKENS added to core/config.py; search() in core/search_index.py takes a snippet_tokens parameter (default 20, validated 1-64, InvalidSearchQueryError on out-of-range) replacing the hardcoded _SNIPPET_TOKENS=12 constant; cli/index.py's search command exposes --snippet-tokens and passes it through. Added core and CLI test coverage for the new default, an explicit value narrowing the excerpt, and the out-of-range error. Verification passed: pdm run pytest -q (651 passed), pdm run ruff check . and ruff format . --diff both clean. Manually smoke-tested the CLI end to end (default, --snippet-tokens 3, and out-of-range 100 all behaved as expected). MCP parity for cac index search remains an accepted, GM-overridden gap per the review log, not addressed by this encounter.
