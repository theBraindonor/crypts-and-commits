---
campaign: v0.1.2-encounter-indexing-and-search
created_by: John Hoff
created_on: '2026-07-27T03:07:56Z'
depends_on:
- build-sqlite-fts5-encounter-index
name: add-index-search-command
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-07-27T03:23:45Z'
---

## Requirements

- New CLI command `cac index search <phrase>`, alongside the existing `cac index status` / `cac index rebuild` in `cli/index.py`.
- Returns a **ranking** of matching results (relevance order) and an **excerpt** of the text that matched, per result.
- Each result also includes the encounter's **name**, **status**, and **last-updated date**.
- Supports `--max-results`/`-n` (default `10`) and `--skip`/`-s` (default `0`) for paging through results.
- Supports `--type`/`-t` to restrict to one document type; default is **all** document types. Only `encounter` is a valid value today (the only `object_type` the index currently stores), but the option and its validation must not hardcode assumptions that block a future type being added.
- **CLI-only, deliberately, this round.** No `mcp/index.py` tool is added for `search`. This is a known, explicit departure from the `cli-mcp-parity` lore, directed by the GM: the search UX (ranking presentation, snippet shape, phrase-query semantics, paging shape) is expected to be tested and refined before it's worth committing to a stable MCP tool contract. MCP coverage is deferred to a follow-up encounter once that shape has settled, using the same durable-exception mechanism already used for `cac index rebuild` (and, for symmetry, `cac index status`) in `build-sqlite-fts5-encounter-index`.
- Read-only: `search` must never create the index file as a side effect (same contract as `cac index status`) - if the index has never been built, say so and point at `cac index rebuild`, the same way `status` does.

## Rationale

`docs/encounter-search-design.md` left `search`'s shape as one of the deferred pieces after `build-sqlite-fts5-encounter-index` stood up the FTS5-backed index, `rebuild`, and `status`. This encounter resolves the remaining open decisions needed for a first, CLI-only `search`:

- **Query semantics.** The command is named `search <phrase>`, not a query-language search - the whole argument is a phrase to find, not an expression the caller composes with FTS5 operators. To honor that (and avoid a raw `sqlite3.OperationalError` surfacing to a user who types something like `C&C` or `test-driven`, both of which contain FTS5 syntax characters), the phrase is wrapped as a single FTS5 phrase-query literal (`"…"`, with internal `"` doubled) before being bound as the `MATCH` parameter. This forces literal, in-order phrase matching and neutralizes any FTS5 operators embedded in user input, rather than letting them be interpreted as query syntax.
- **Ranking.** FTS5's built-in `bm25()` ranking function orders hits; the command surfaces this as a 1-based rank number per result (`offset + position`), not the raw BM25 score, since the score itself isn't a meaningful number to show a user - only the resulting order is.
- **Excerpt.** FTS5's `snippet()` function generates a short, query-centered excerpt from the matched `body` column (with `**…**` markers around matched terms, a plain-text convention - not Rich markup - since excerpt text originates from stored encounter bodies and must be printed with `markup=False` per `console-best-practices`, same as every other command that prints stored content).
- **Metadata needed for display (name/status/updated date) requires a schema change.** The existing `sourcebook_fts` table (from `build-sqlite-fts5-encounter-index`) stores `object_type, campaign, name, status, body` but not `updated_on`. This encounter adds `updated_on` as a new `UNINDEXED` column, populated during `rebuild_index` from the same frontmatter `encounter_core.read_metadata` already exposes (no change to the public `Encounter` dataclass - `_reindex_encounters` reads `updated_on` directly from the metadata dict instead of extending a dataclass that's used across the whole `core.encounter` surface for other, unrelated purposes). Because the index is fully regenerable, git-ignored, derived data (per the prior encounter's Requirements) and `rebuild_index` always does a full drop-and-recreate, this schema change carries no migration burden - the next `cac index rebuild` picks it up automatically; a stale on-disk index from before this change simply predates the new column until rebuilt, the same staleness tradeoff already accepted for index/write-path drift generally.
- **Type filter.** `object_type` is already a stored, filterable (if `UNINDEXED`) column per the existing schema's forward-looking design ("Schema must not be encounter-specific"). `--type` filters on it directly; an unrecognized value is rejected with the current valid set listed, read from a new `SEARCH_INDEX_OBJECT_TYPES` list in `config.py` (today just `[SEARCH_INDEX_OBJECT_TYPE_ENCOUNTER]`) rather than a hardcoded check, so a later encounter adding a new indexed type only has to extend that list.
- **Response budget.** `docs/encounter-search-design.md` calls for search results to obey the project's 20,000-character MCP response budget (`budget_core`). That applies to the eventual MCP tool's payload, not this encounter's human-facing console output - `--max-results`/`--skip` are the CLI's own pacing mechanism instead. Wiring `search` results through `budget_core` is left for the follow-up MCP encounter noted above, alongside adding the MCP tool itself.

`clean-tests-and-lint` and `console-best-practices` (both assigned to the `crypts-and-commits` region) apply and are honored as described above.

## Plan

1. **`core/config.py`**: add `SEARCH_INDEX_OBJECT_TYPES = [SEARCH_INDEX_OBJECT_TYPE_ENCOUNTER]` (the currently-valid `--type` values) and `SEARCH_DEFAULT_MAX_RESULTS = 10`.
2. **`core/search_index.py`**:
   - Extend `_CREATE_TABLE_SQL` with an `updated_on UNINDEXED` column, positioned before `body` (so `body`'s column index for `snippet()` becomes `5`).
   - Update `_reindex_encounters` to call `encounter_core.read_metadata(root, campaign, name)` instead of `read_encounter`, and insert `status`/`updated_on` from the returned metadata dict and `body` from the returned content string (campaign/name already known from the loop).
   - Add a frozen `SearchHit` dataclass: `rank: int, object_type: str, campaign: str, name: str, status: str, updated_on: str, excerpt: str`.
   - Add exceptions `EmptySearchPhraseError(ValueError)` and `InvalidSearchQueryError(ValueError)`.
   - Add `search(root, phrase, *, object_type=None, limit=SEARCH_DEFAULT_MAX_RESULTS, offset=0) -> list[SearchHit] | None`:
     - Validate `phrase.strip()` is non-empty (else `EmptySearchPhraseError`), `limit >= 1` and `offset >= 0` (else `InvalidSearchQueryError`), and `object_type in SEARCH_INDEX_OBJECT_TYPES` when given (else `InvalidSearchQueryError` listing the valid set).
     - Return `None` if `search_index_db_path(root)` doesn't exist yet - same "never built" contract as `index_counts`, and for the same reason: a search is a read, and must not create the index file as a side effect.
     - Otherwise open a fresh, short-lived connection (read-only use, same non-cached lifecycle as every other function in this module), build the FTS5 phrase-literal MATCH string described in Rationale, run a `SELECT campaign, name, status, updated_on, snippet(sourcebook_fts, 5, '**', '**', '...', 12), bm25(sourcebook_fts) FROM sourcebook_fts WHERE sourcebook_fts MATCH ? [AND object_type = ?] ORDER BY bm25(sourcebook_fts) LIMIT ? OFFSET ?`, close the connection, and return the rows as `SearchHit`s with `rank = offset + position`.
3. **`cli/index.py`**: add a `search` command:
   - `phrase: str = typer.Argument(...)`, `max_results: int = typer.Option(10, "--max-results", "-n")`, `skip: int = typer.Option(0, "--skip", "-s")`, `object_type: str | None = typer.Option(None, "--type", "-t")`.
   - Call `search_index_core.search(...)`, catching `EmptySearchPhraseError` / `InvalidSearchQueryError` and routing to `fail(console, str(exc))`.
   - `None` result -> print the same "No index has been built yet. Run `cac index rebuild`..." message `status` already prints.
   - Empty list -> `console.print(f"No results for {phrase!r}.", markup=False)` (embeds free-form user input, so no markup per `console-best-practices`).
   - Otherwise, for each hit print a `#{rank}  {name}  [{status}]  updated {updated_on}` line followed by an indented excerpt line, both `markup=False` (name/excerpt are stored content).
   - If the page was full (`len(hits) == max_results`), print a `[dim]` hint (CLI-authored, markup is fine) suggesting `--skip {skip + max_results}` for the next page.
4. **Tests**:
   - `tests/core/test_search_index.py`: `search` returns `None` before any rebuild; returns `[]` for a non-matching phrase; finds a phrase across multiple encounters/campaigns with correct `name`/`status`/`updated_on`/non-empty `excerpt`; a phrase containing FTS5-special characters (e.g. a hyphen or a literal `"`) does not raise `sqlite3.OperationalError` and matches (or cleanly misses) literally; `object_type="encounter"` filters correctly and an unknown type raises `InvalidSearchQueryError`; `limit`/`offset` page correctly with `rank` reflecting absolute position across pages; blank phrase raises `EmptySearchPhraseError`; `limit < 1` / `offset < 0` raise `InvalidSearchQueryError`.
   - `tests/cli/test_index.py`: `cac index search` before rebuild reports "No index has been built yet"; after rebuild, a matching phrase shows rank/name/status/updated/excerpt; a non-matching phrase reports no results; `--max-results`/`--skip` narrow the page; an invalid `--type` exits non-zero with a clear message.

## Verification

- `pdm run pytest -q` passes, including the new/updated tests above, with no skips or deletions used to dodge a failure.
- `pdm run ruff check .` reports zero errors and `pdm run ruff format .` reports no diffs.
- Manually run `cac index rebuild` against this repo's own `.sourcebook`, then `cac index search` for a distinctive phrase known to appear in an existing encounter body (e.g. a term from `build-sqlite-fts5-encounter-index`'s own text) and confirm the rank, name, status, updated date, and excerpt all look correct and the excerpt actually contains the matched text.
- Manually exercise `--type encounter`, an invalid `--type` value (expect a clean non-zero-exit error, not a stack trace), `--max-results 1`, and `--skip 1` against the rebuilt index.

## Log

### Review - 2026-07-27T03:12:42Z - John Hoff

Plan honors clean-tests-and-lint (Verification section matches the gate verbatim) and console-best-practices (correctly distinguishes stored/user-sourced text requiring markup=False — including the snippet() **…** markers and the phrase-embedding 'no results' message — from CLI-authored, markup-safe strings). It knowingly departs from cli-mcp-parity by shipping search as CLI-only, but that lore explicitly permits an exception when the Plan justifies the gap, and this one does: GM-directed, reasoned (UX not yet stable enough for a committed MCP contract), and scoped to a named follow-up encounter for MCP coverage. Two points are noted rather than blocking: the claimed precedent for this 'durable-exception mechanism' in build-sqlite-fts5-encounter-index wasn't independently verifiable within this review's bounded reading surface, and the numbered Plan doesn't show any code-level step recording the exception if such a registry exists beyond encounter-body documentation. Recommend proceeding, with a quick confirmation from the GM that no such registry needs a companion edit.

### Message - 2026-07-27T03:20:44Z - John Hoff

Refined the result line format after seeing real output: added the raw bm25() relevance score to `SearchHit` (new `score: float` field, selected alongside the existing columns) and print it immediately after the rank and before the name - `#{rank}  {score:.3f}  {name}  [{status}]  updated {updated_on}`. This wasn't in the reviewed Plan's line format but is a same-scope refinement of the already-approved "return the ranking of the results" requirement, not a new capability. No lore-relevant behavior changed (still CLI-only, still markup=False for all stored/derived text).

### Completed - 2026-07-27T03:23:45Z - John Hoff

Verification passed: pdm run pytest -q (596 passed, no skips), ruff check . and ruff format . --check both clean. Manually rebuilt this repo's own .sourcebook (28 encounters indexed), then exercised cac index search: a distinctive phrase correctly returned rank/score/name/status/updated/excerpt with the excerpt containing the matched text; --type encounter filtered correctly and --type bogus failed cleanly (exit 1, no stack trace); --max-results/--skip paged correctly with the "more results" hint. Post-review refinement (recorded as a message): added a raw bm25() score field to SearchHit, printed before the name per GM request after seeing live output. Confirmed near-zero scores for very common terms (e.g. "encounter") are expected BM25 behavior (IDF collapses for terms present in nearly every document in this self-referential corpus), not a bug - rank order remains correct regardless of display rounding.
