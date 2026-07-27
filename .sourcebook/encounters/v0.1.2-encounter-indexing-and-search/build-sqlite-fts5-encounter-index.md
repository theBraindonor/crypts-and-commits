---
campaign: v0.1.2-encounter-indexing-and-search
created_by: John Hoff
created_on: '2026-07-27T02:18:58Z'
depends_on: []
name: build-sqlite-fts5-encounter-index
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-07-27T02:56:47Z'
---

# Build SQLite FTS5 Encounter Index

## Requirements

- Resolve the engine choice left open in `docs/encounter-search-design.md`: use SQLite FTS5 via the stdlib `sqlite3` module (verified available in this environment: `CREATE VIRTUAL TABLE ... USING fts5(...)` succeeds with the project's Python). No new dependency.
- Build a durable, on-disk full-text index, **synced by full rebuild against `.sourcebook` on disk, not by hooking individual encounter writes.** This is a deliberate simplification over the design doc's write-path-hook idea: fewer files touched (no changes anywhere in `core/encounter.py`), and a rebuild-from-disk is far easier to test and verify than asserting index state after every one of an encounter's eight mutating operations. Staleness between rebuilds is an accepted tradeoff for this first cut, not an oversight - incremental sync tied to the write path is left as a possible later encounter if rebuild-only proves too coarse in practice.
- **Schema must not be encounter-specific.** The table/module shape must not hardcode "encounter" into every symbol, so a later encounter can add other object types (starting with campaigns) without a rename or migration. Whether lore/region/world ever join search is explicitly **not** decided here - the design doc's existing call (they stay out, being small/bounded/resolved-by-assignment) still stands unless a future encounter revisits it.
- **Cross-process safety.** The index must be safely readable by a consumer running in a different OS process than the one that wrote it. Every write must fully commit and close its connection within the same function call; no connection or transaction may be held open across calls or cached at module scope. A reader opening a fresh connection immediately after a write returns must see the committed state.
- **`cac index rebuild`** - a new CLI command that fully rebuilds the index from the encounters found on disk under `.sourcebook`. Always a full drop-and-reindex; no merge or partial-update logic at this time.
- **`cac index status`** - a new CLI command that reports how many items are indexed, broken down by type. For this encounter that means a single `encounter` count, since encounters are the only object type wired up. Must not silently create the index file as a side effect of a read (a status check is read-only); if the index has never been built, say so and point at `cac index rebuild` rather than reporting a misleading zero.
- The index is derived data: regenerable from `.sourcebook` content alone, stored outside version control.
- **No MCP tool for either command in this encounter** - see Rationale for why, and what would need to be true before adding one.

## Rationale

`docs/encounter-search-design.md` (deferred design notes, written during the `v0.1.1-mcp-transition` campaign) already resolved the shape of this problem: encounters are a growing, freeform corpus that needs relevance-ranked search, not deterministic graph traversal like lore/region/world, and search must be backed by a real index, not a per-query scan. It leaves six decisions open before implementation, plus proposes tying index sync to the write path. This encounter revises that sync approach and resolves the pieces needed to stand up the index and a rebuild/status surface, deferring `search`/`get` to a later encounter:

- **Engine (open decision 1)** - resolved: SQLite FTS5. Zero external service, ships with Python's `sqlite3`, adequate BM25-style ranking (`bm25()`) for a first cut. Confirmed the interpreter's `sqlite3` build includes the FTS5 extension.
- **What is indexed (open decision 2)** - resolved for this cut: index each object's full body as one field (not split into sub-sections) plus `object_type`, `campaign`, `name`, and `status` as unindexed, filterable columns. `object_type` generalizes the table past encounters per GM direction (see Requirements), even though this encounter only ever writes rows with `object_type = "encounter"`.
- **Index sync model (revises the design doc's write-path-hook proposal, per GM direction)** - resolved: full rebuild-from-disk via `cac index rebuild`, not incremental hooks in `core/encounter.py`. This trades always-fresh for simplicity: no risk of an encounter mutation path being missed by a hook, no coupling between `core/encounter.py` and the index module, and verification reduces to "rebuild produces the expected count/content from what's on disk" rather than asserting index deltas after each of `create`/`update`/`review`/`open`/`complete`/`abandon`/`record-message`/region/dependency changes. The obvious cost - the index can lag behind the latest write until the next rebuild - is accepted for this first cut.
- **Index location & lifecycle (open decision 5)** - resolved: `<sourcebook_dir>/.index/sourcebook.db`, added to the root `.gitignore` (`.sourcebook/.index/`). Colocated with the content it derives from, clearly marked as internal (dot-prefixed) rather than domain content, git-ignored since it's regenerable. `cac index rebuild` is exactly the "rebuild/reindex command for cold builds and recovery" the design doc calls out - it's just also the *only* sync mechanism now, not a fallback to an incremental one.
- **Cross-process readability** (raised by GM review, not one of the doc's six numbered decisions but load-bearing here): connections are never cached or held open across calls - every index operation is a self-contained connect -> write -> commit -> close within one function. `PRAGMA journal_mode=WAL` is set on connect to reduce reader/writer blocking between processes/sessions.
- **Surface (open decision 6)** - partially resolved: CLI (`cac index status` / `cac index rebuild`), no MCP tool yet. This is a deliberate gap in `cli-mcp-parity` (the `crypts-and-commits` region's assigned lore, which normally requires every CLI command to have a matching MCP tool, `bootstrap` being the one standing exception): `cac index rebuild` walks and reindexes every encounter in every campaign, a potentially long-running, full-corpus operation, and MCP tool calls are a request/response shape not well suited to an unbounded-duration call. Making it an MCP tool now would either block an agent's MCP session for however long a rebuild takes, or require a background/async job pattern this project doesn't have yet. Formalizing this as a durable exception (parallel to `bootstrap`'s developer-only one) belongs in a follow-up that edits `cli-mcp-parity`'s body directly, once the shape of that exception is settled - not rushed alongside this encounter's implementation. `cac index status` has no such long-running concern and could reasonably get an MCP tool later without needing that lore change first; it's held back in this encounter only for symmetry with `rebuild` and to keep this encounter's surface change to one clearly-scoped exception rather than a partial one.
- **Ranking/snippet (open decision 4)** is still irrelevant until a `search` call exists.
- **Search scope (open decision 3)** doesn't need resolving to build the index - the schema already stores `campaign` and `status` per row.

`console-best-practices` (also assigned to `crypts-and-commits`) is honored: both new commands' `console.print` output is CLI-authored (counts, status messages), not stored `.sourcebook` content, so the default `markup=True` is fine and no `markup=False` call is needed.

## Plan

1. **Config additions** (`core/config.py`): `SEARCH_INDEX_DIR_NAME = ".index"`, `SEARCH_INDEX_DB_NAME = "sourcebook.db"`, `SEARCH_INDEX_FTS_TABLE = "sourcebook_fts"`, `SEARCH_INDEX_OBJECT_TYPE_ENCOUNTER = "encounter"` (the only `object_type` value written by this encounter).
2. **Path helper** (`core/paths.py`): `search_index_db_path(root) -> Path` returning `sourcebook_dir(root) / SEARCH_INDEX_DIR_NAME / SEARCH_INDEX_DB_NAME`.
3. **New module `core/search_index.py`** (deliberately not named around encounters):
   - A `_connect(root)` helper: opens a new connection each call (creating the parent `.index/` dir as needed), sets `PRAGMA journal_mode=WAL`, and ensures the schema exists: `CREATE VIRTUAL TABLE IF NOT EXISTS sourcebook_fts USING fts5(object_type UNINDEXED, campaign UNINDEXED, name UNINDEXED, status UNINDEXED, body, tokenize='porter unicode61')`. Every public function opens its own connection via this helper, commits, and closes before returning - none is held open across calls or stored at module scope.
   - `rebuild_index(root) -> int` - connect, drop and recreate the table, walk every campaign (`campaign_core.list_campaigns`) and every encounter within it (`list_encounters` + `read_encounter`), insert a row per encounter with `object_type="encounter"`, commit, close, and return the total count indexed. Structured (a small per-type reindex step) so a later encounter can add a campaigns/etc. pass without restructuring this function.
   - `index_counts(root) -> dict[str, int] | None` - if `search_index_db_path(root)` does not exist on disk, return `None` (signals "never built" without creating the file as a read side effect). Otherwise connect, run `SELECT object_type, COUNT(*) FROM sourcebook_fts GROUP BY object_type`, close, and return the counts as a dict.
4. **New CLI module `cli/index.py`**: a Typer sub-app with `status` and `rebuild` commands, following the existing thin-wrapper pattern (`cli/world.py` as reference) - call straight into `core/search_index.py`, print results via `rich.Console`. `status` prints "no index built yet, run `cac index rebuild`" when `index_counts` returns `None`; otherwise prints the total and the per-type breakdown. `rebuild` prints the resulting count. Register in `cli/app.py` as `app.add_typer(index_app, name="index")`.
5. **`.gitignore`**: add `.sourcebook/.index/`.
6. **Tests**:
   - `tests/core/test_search_index.py` - unit tests for `rebuild_index` and `index_counts` against a temporary `.sourcebook` root: rebuild picks up encounters created via `core/encounter.py` across multiple campaigns; a second `rebuild_index` call after adding/removing encounters reflects the new on-disk state (proving it's a true drop-and-reindex, not additive); `index_counts` returns `None` before any rebuild and correct counts after; a cross-process-style visibility case (rebuild via the module's normal call path, then open a second, independent `sqlite3.connect()` directly against the same file and confirm it reads the committed rows without coordination); confirm no connection/cursor object is returned or leaked across calls.
   - `tests/cli/test_index.py` - `CliRunner` tests for `cac index status` (before and after a rebuild) and `cac index rebuild`, following the existing pattern in `tests/cli/test_world.py`.

## Verification

- `pdm run pytest -q` passes, including the new tests above, with no skips or deletions used to dodge a failure.
- `pdm run ruff check .` reports zero errors and `pdm run ruff format .` reports no diffs.
- Manually run `cac index status` (expect "no index built yet"), then `cac index rebuild` against this repo's own `.sourcebook`, then `cac index status` again and confirm the reported encounter count matches reality (sum of `cac encounter list` across all campaigns).
- Confirm the cross-process visibility test passes: a second, independent connection to the same database file sees a rebuild's writes immediately after `rebuild_index` returns, with no held-open connection anywhere in `search_index.py`.

## Log

### Review - 2026-07-27T02:48:02Z - John Hoff

GM OVERRIDE of an independent-reviewer REJECT verdict. The reviewer found a conflict with `cli-mcp-parity`: the Plan adds `cac index status` and `cac index rebuild` to the CLI with no matching MCP tools, and judged the Rationale's justification insufficient - specifically that `status`'s gap is held back only "for symmetry" with `rebuild` rather than its own merits, and that `rebuild`'s long-running-operation justification defers formalizing the exception into `cli-mcp-parity` itself to a later encounter instead of resolving it now. The reviewer also confirmed `clean-tests-and-lint` and `console-best-practices` are honored, with no other findings.

The GM has reviewed this conflict and confirms it was a known, deliberate tradeoff at draft time, not a new issue surfaced by review: CLI-only for both commands this round, with the `cli-mcp-parity` lore amendment for a long-running-task exception explicitly deferred to a follow-up. No changes to the Plan follow from this override. Proceeding to `reviewed` on GM authority per CLAUDE.md's retained-final-authority framing, departing from the skill's normal auto-transition-on-PASS-WITH-NOTES-only process.

### Completed - 2026-07-27T02:56:47Z - John Hoff

Verification passed: pdm run pytest -q (582 passed, including 9 new tests in tests/core/test_search_index.py and tests/cli/test_index.py), ruff check . and ruff format . --check both clean. Manually ran cac index status (no index yet) -> cac index rebuild (27 items indexed) -> cac index status (confirmed 27, encounter: 27), cross-checked against the actual per-campaign encounter counts (17+9+1+0+0=27). Confirmed .sourcebook/.index/ is git-ignored (absent from git status) while sourcebook.db exists on disk. Cross-process visibility and no-held-open-connection behavior covered by test_index_visible_to_a_second_independent_connection and the rebuild_index/index_counts implementation (self-contained connect/commit/close per call, WAL journal mode).
