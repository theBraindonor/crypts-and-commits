---
archived: true
campaign: v0.1.2-encounter-indexing-and-search
created_by: John Hoff
created_on: '2026-07-27T05:37:43Z'
depends_on: []
name: sync-index-on-write
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-08-02T22:13:48Z'
---

## Requirements

Keep `.sourcebook/.index/sourcebook.db` continuously in sync with `.sourcebook` content as it is created, updated, or deleted through `cac` - without requiring a separate `cac index rebuild` call after every change - so the index stays current with local, cac-mediated edits automatically. Concretely:

- Every core mutation that creates, updates, or deletes an indexed object (encounter, world, lore, region) must incrementally patch `sourcebook.db` within the same call, with no additional command needed.
- This must be transparent to both the CLI and the MCP server: neither `cli/` nor `mcp/` may need any code change, since both are thin wrappers that already call straight into `core/` - the sync has to live at the `core` layer to cover both by construction.
- No auto-vivification: if `sourcebook.db` has never been built (`cac index rebuild` has never run), incremental sync must remain a no-op, exactly preserving today's "index has never been built" signal from `index_counts()`/`search()` (both return `None`). A repo that hasn't opted into the index yet must not silently gain a partial one.
- `cac index rebuild` (`search_index.rebuild_index()`) keeps its current behavior unchanged: a full drop-and-reindex from `.sourcebook` on disk. It remains necessary for (a) the first-ever build of the index, and (b) resynchronizing after content changes `cac` didn't make itself - `git pull`, branch checkout, merge, or a manually-edited file.
- Campaigns stay out of scope for indexing, matching today's behavior (`SEARCH_INDEX_OBJECT_TYPES` covers only `encounter`/`world`/`lore`/`region`) - campaign writes/deletes must not error just because campaigns aren't an indexed type.
- No import cycle between `cac.core.search_index` and the domain modules (`encounter`, `campaign`, `lore`, `region`, `world`) it will now be invoked from.
- **Concurrency**: multiple `cac` processes must be able to run against the same project's `.sourcebook` at once - multiple MCP server instances (e.g. separate agent sessions) and/or CLI invocations - without incremental sync from one process breaking or blocking another's. Concretely:
  - Each incremental sync (`sync_write`/`sync_delete`) must open its own connection, perform one small transaction (its DELETE-then-INSERT, or its DELETE, plus commit), and close - never hold a connection open across calls, across multiple sync operations, or for the lifetime of a process (no cached/module-level/singleton connection). This is the same discipline `_connect()` already documents and follows for `rebuild_index`/`search`/`index_counts`; incremental sync must not regress it by, e.g., threading a shared connection through the `core` write path for convenience.
  - Concurrent *writers* from separate processes are a real case now (two agent sessions editing the same project at once), not a theoretical one - SQLite still only allows one writer transaction at a time even in WAL mode, so a second process's brief write can otherwise fail immediately with "database is locked". That must become a short, bounded wait-and-retry (a busy timeout), not a hard failure, since today's markdown-file writes have no equivalent shared-lock contention at all - adding a shared SQLite index to the write path must not make ordinary concurrent use of the sourcebook less reliable than it is today.

## Rationale

Today the index only reflects reality in the instant right after `cac index rebuild` runs; every `cac`-driven change since then is invisible to `index_search`/`index_status` until someone remembers to rebuild. That's an easy step to forget and a silent staleness risk for exactly the workflow the index exists to serve (an agent searching past encounters/lore/regions to build context). Making writes self-maintaining removes that operational burden for the common case, while `rebuild` remains for the one case incremental sync structurally can't cover: content that changed outside `cac`'s own write path.

This is tractable in a small, contained change because every mutating `core` function already funnels through two choke points: `frontmatter_utils.write_post(path, post)` for writes, and a raw `path.unlink()` for deletes (four call sites: `encounter.delete_encounter`, `campaign.delete_campaign`, `lore.delete_lore`, `region.delete_region`). Hooking those two spots, rather than each of the ~20 individual call sites across five `core` modules, keeps the change small and guarantees no current or future mutation path is missed.

The main risk is a `core.search_index` <-> domain-module import cycle, since `search_index.py` already imports `encounter`/`campaign`/`lore`/`region`/`world` (as `*_core`) at module level to drive `rebuild_index()`, and the domain modules would need to import `search_index` back to call the new sync functions. This is resolved by moving those five imports out of `search_index.py`'s module level and into `rebuild_index()`'s own body (they're only ever used inside that function and its `_reindex_*` helpers), so `search_index.py`'s import-time surface has zero dependency on the domain modules once this lands.

The second risk, concurrency, is new because this encounter is the first thing to put a shared SQLite file into the ordinary write path. `.sourcebook`'s markdown files are already safe under multiple simultaneous `cac` processes in practice (each object is its own file, and nothing today reads-then-writes across a network of shared state), but `sourcebook.db` is one file every process's writes now funnel through. Two habits keep that safe: keeping each sync's connection and transaction as small and short-lived as possible (so the exclusive write lock is held for the shortest possible window), and setting a busy timeout so a second process's write waits briefly for the first's short transaction to finish rather than failing outright the instant it collides with it.

## Plan

1. In `packages/crypts-and-commits/src/cac/core/search_index.py`, move the five `from cac.core import X as X_core` domain imports (`campaign`, `encounter`, `lore`, `region`, `world`) from module level into the body of `rebuild_index()` (or its `_reindex_*` helpers) - purely a relocation, no behavior change - so the module has no domain-module dependency at import time.
2. In `_connect()`, add `conn.execute("PRAGMA busy_timeout = <N>")` (a new `SEARCH_INDEX_BUSY_TIMEOUT_MS` constant in `core/config.py`, e.g. 5000ms) alongside the existing `PRAGMA journal_mode=WAL`, so every connection this module opens - `rebuild_index`, `search`, `index_counts`, and the new sync functions below - waits up to that timeout for a lock instead of raising `sqlite3.OperationalError` immediately when another process holds the write lock.
3. Add to `search_index.py`:
   - A path classifier using the existing `LORE_DIR_NAME` / `REGION_DIR_NAME` / `ENCOUNTER_DIR_NAME` / `CAMPAIGN_DIR_NAME` / `WORLD_FILE_NAME` constants (`core/config.py`) plus `sourcebook_dir()` (`core/paths.py`) that maps a `.sourcebook`-relative file path to `(object_type, campaign, name)`. Returns `None` for paths under `campaigns/` (not an indexed type) or anything unrecognized, so callers can no-op.
   - `sync_write(root: Path, path: Path, post: frontmatter.Post) -> None`: return immediately if `search_index_db_path(root)` doesn't exist yet (no auto-vivification). Otherwise classify `path`; if unclassified, return. Derive `status` the same way each existing `_reindex_*` helper already does for that object type (lore's enabled/disabled flag off `post.get("enabled", True)`; empty string for world/region; `post.get("status", "")` for encounter), and `name`/`campaign`/`body`/`updated_on` from `post`/the classified path. Open one connection via `_connect()`, run `DELETE FROM sourcebook_fts WHERE object_type = ? AND campaign = ? AND name = ?` for any existing row followed by the `INSERT` of the fresh row as a single transaction, commit, and close - all within this one function call, no connection or transaction held open beyond it.
   - `sync_delete(root: Path, path: Path) -> None`: same existence and classification checks (using the path alone, no `post` available), then one connection, one `DELETE` transaction, commit, close - same lifecycle as `sync_write`.
   - Both reuse the existing `_connect()` helper (safe once file existence is already confirmed - its `mkdir`/`CREATE TABLE IF NOT EXISTS` become no-ops) and follow the same connect/act/commit/close-within-one-function lifecycle already documented on `_connect`, now with the busy timeout from step 2 backing it under concurrent access.
4. In `packages/crypts-and-commits/src/cac/core/frontmatter_utils.py`:
   - Change `write_post(path: Path, post: frontmatter.Post)` to `write_post(root: Path, path: Path, post: frontmatter.Post)`; after the existing `path.write_text(...)`, call `search_index.sync_write(root, path, post)`.
   - Add `delete_post(root: Path, path: Path) -> Path`: `path.unlink()`, then `search_index.sync_delete(root, path)`, then `return path`.
5. Update every `write_post(path, post)` call site (`encounter.py`, `campaign.py`, `lore.py`, `region.py`, `world.py` - roughly 17 sites total) to `write_post(root, path, post)`; `root` is already in scope at each one.
6. Replace the four `path.unlink(); return path` sequences (`encounter.delete_encounter`, `campaign.delete_campaign`, `lore.delete_lore`, `region.delete_region`) with `return delete_post(root, path)`.
7. No changes needed in `cli/` or `mcp/` - both call straight into the `core` functions touched above, so the sync is transparent to both by construction, satisfying `cli-mcp-parity` (neither surface diverges - both just keep working, unmodified).

## Verification

- `pdm run pytest -q` (full suite) passes.
- `pdm run ruff check .` passes with zero errors; `pdm run ruff format .` leaves no diff.
- New tests (likely in `tests/core/test_search_index.py`, alongside the existing `rebuild_index`/`search` coverage) verifying:
  - After one `rebuild_index()`, `create_encounter`/`update_encounter`/`delete_encounter` are each immediately reflected in `search()` results with no further `rebuild_index()` call.
  - Same immediate-reflection check for `lore` and `region` create/update/delete, and for `world`'s `set_attribute`/`update_body`/`assign_lore`/`unassign_lore` (update only - world has no delete).
  - Before any `rebuild_index()` has ever run, calling `create_lore`/`create_region`/`create_encounter`/`world.initialize_world` does not create `sourcebook.db` - `index_counts()` still returns `None` afterward (no auto-vivification).
  - Deleting a campaign does not raise and leaves the index table untouched (campaigns aren't an indexed type).
  - A simulated external change (write a `.sourcebook` file directly on disk, bypassing `cac`, standing in for a `git pull`) is absent from `search()` results until `rebuild_index()` runs, and present afterward - confirming `rebuild` is still the mechanism for catching up on non-`cac`-driven changes.
  - Concurrency: with one connection deliberately holding an open write transaction against `sourcebook.db` (simulating a second process's in-flight sync), a `sync_write`/`sync_delete` call from a second connection succeeds once the first commits, within the busy timeout, rather than raising `sqlite3.OperationalError: database is locked` immediately.
- Manual smoke check: after a `rebuild_index()`, run `pdm run cac lore create ...` (or the MCP `lore_create` tool), then `pdm run cac index search ...` (or MCP `index_search`) and confirm the new entry is found without an intervening `cac index rebuild`.

## Log

### Review - 2026-07-27T06:01:56Z - John Hoff

Reviewed against all three applicable lore items (clean-tests-and-lint, cli-mcp-parity, console-best-practices) and cross-checked the Plan's technical claims directly against search_index.py, frontmatter_utils.py, paths.py, config.py, and representative call sites in lore.py/world.py/encounter.py: every claim (current write_post signature, _connect() behavior, index_counts/search None-guards, the import-cycle risk and its fix, dir-name constants, and root being in scope at all ~26 write/delete call sites) checks out against the actual code, and grep confirms cli/ and mcp/ never call write_post/unlink directly, so the "no cli/mcp changes needed" claim under cli-mcp-parity is correct rather than assumed. Verification section satisfies clean-tests-and-lint with full-suite pytest, ruff, and specific new-behavior tests including the no-auto-vivification and campaign-exclusion guarantees the Requirements demand. Only a trivial call-site-count estimate (17 vs. an actual 26) is off, which doesn't affect the design. No lore conflicts found; approved to proceed to reviewed.

### Completed - 2026-07-27T23:10:50Z - John Hoff

Implemented as planned: search_index.py's four domain-module imports moved into their respective _reindex_* helpers (no import cycle - verified by importing the whole cac.core package cleanly), a busy_timeout PRAGMA added via _connect(), a path classifier, and sync_write/sync_delete each using one short _connect()-scoped transaction. write_post/delete_post added to frontmatter_utils.py and wired through all ~26 write/delete call sites across encounter.py, campaign.py, lore.py, region.py, and world.py. No cli/ or mcp/ changes were needed. Verification: pdm run pytest -q (672 passed), ruff check . clean, ruff format . no diff, new tests covering immediate reflection for all four indexed types' create/update/delete, no-auto-vivification before any rebuild, campaign delete being a no-op for the index, external-change staleness until rebuild, and a concurrency test (a second connection's held write transaction causes a wait-then-succeed rather than an immediate failure). Manual smoke test in a disposable scratch project confirmed cac lore create after one rebuild is found by cac index search with no intervening rebuild.
