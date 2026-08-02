---
campaign: v0.1.6-archive-campaigns-and-encounters
created_by: John Hoff
created_on: '2026-08-02T18:18:05Z'
depends_on: []
name: add-campaign-to-search-index
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-08-02T20:48:16Z'
---

## Requirements

- Fix a coverage gap in the SQLite FTS5 search index (`core/search_index.py`): campaigns are not indexed today. `SEARCH_INDEX_OBJECT_TYPES` is currently `(encounter, world, lore, region)` — `add-world-lore-region-to-search-index` (v0.1.2) extended indexing from encounter-only to those three, but campaigns were never added, and `_classify()` explicitly treats `campaigns/` as "not an indexed type." No design doc argues campaigns should deliberately stay excluded — this is an oversight, not a decision, identified by the GM while scoping this campaign's archiving work.
- Add a fourth `object_type`: `campaign`, via a new `SEARCH_INDEX_OBJECT_TYPE_CAMPAIGN = "campaign"` constant appended to `SEARCH_INDEX_OBJECT_TYPES` in `core/config.py`. No schema/DDL change — the existing `object_type`/`campaign`/`name`/`status`/`updated_on`/`body` columns already generalize, same as the prior world/lore/region extension.
- `rebuild_index` must add a campaign pass: one `campaign` row per name in `campaign_core.list_campaigns(root)`, alongside the existing encounter/world/lore/region passes.
- Column semantics for the new `campaign` object type:
  - `campaign` column — empty string. This column means "the campaign an encounter belongs to"; a campaign is not scoped to another campaign, so leaving it unset mirrors how world/lore/region already leave it unset (their `name` column already carries the identifying name).
  - `status` — the campaign's real lifecycle status (`draft`/`open`/`paused`/`completed`/`abandoned`), read via `metadata.get("status", "")`, matching the exact pattern `_reindex_encounters` already uses (not a new default-value convention).
  - `name` — the campaign's file-stem name, same as every other type.
  - `updated_on` — the campaign's own `updated_on` frontmatter field.
- `_classify()` must recognize `campaigns/<name>.md` (`len(parts) == 2 and parts[0] == CAMPAIGN_DIR_NAME`) and map it to `(SEARCH_INDEX_OBJECT_TYPE_CAMPAIGN, "", path.stem)`, so `sync_write`/`sync_delete` — already wired generically off `_classify` inside `frontmatter_utils.write_post`/`delete_post` — start picking up campaign create/update/status-transition/delete without any further code change. Update `_classify`'s docstring/comment, which currently states paths under `campaigns/` return `None` "(not an indexed type)" — that becomes false.
- No status-lifecycle guard changes anywhere else (`core/campaign.py` untouched) — this encounter only makes existing campaign writes visible to the index; it does not change what campaign operations are allowed or when.
- No CLI (`cli/index.py`) or MCP (`mcp/index.py`) changes — both already generalize over whatever `object_type` values exist (`--type`/`object_type` validates against `SEARCH_INDEX_OBJECT_TYPES` generically; `index status` iterates whatever keys `index_counts` returns), the same precedent `add-world-lore-region-to-search-index` established and confirmed still holds.
- Test fallout: nearly every existing test in `tests/core/test_search_index.py` creates at least one campaign via its `_make_campaign` helper as setup for an encounter, so once campaigns are indexed, a wide set of existing `count`/`index_counts()` assertions will be off by the number of campaigns each test creates and must be corrected in place, not worked around. Two existing tests assert the *current* (soon to be wrong) exclusion directly and need rewriting rather than just a number tweak:
  - `test_search_unknown_object_type_raises` currently uses `object_type="campaign"` as its example of an invalid type — `"campaign"` becomes valid, so it needs a different, still-invalid example string.
  - `test_delete_campaign_does_not_touch_index` currently documents that deleting a campaign leaves the index untouched — once campaigns are indexed, deleting one removes its own campaign row (via the same generic `sync_delete` path lore/region deletion already uses) while leaving any encounters nested under it alone. Rewrite this test (and rename it) to assert that corrected behavior instead of the old exclusion.
  - `tests/cli/test_index.py` and `tests/mcp/test_index.py` similarly set up a campaign as fixture scaffolding for encounter tests; any assertions on total/per-type counts need the same correction.
- New coverage to add (mirroring the existing per-type test shape already used for encounter/world/lore/region): `rebuild_index` indexes campaigns and includes them in its returned count and in `index_counts()`; `search()` finds a phrase unique to a campaign body and returns a hit with the right `name`/`status`/`updated_on`, and filters correctly with `object_type="campaign"`; a freshly created campaign is immediately searchable without an intervening rebuild (incremental `sync_write` on create); a campaign's indexed `status` reflects a status transition (e.g. `campaign_open`) without an intervening rebuild; a deleted campaign's row disappears from the index immediately (incremental `sync_delete`) while its encounters' rows are unaffected.

## Rationale

This campaign's body flags "how `search_index.py` stays consistent" as a design question archiving needs to resolve, on the assumption that campaigns already participate in the index the way encounter/world/lore/region do. They don't — `_classify()` hard-excludes `campaigns/` today, a gap that predates this campaign and traces back to `add-world-lore-region-to-search-index`, which only closed the world/lore/region half of that extension and left campaigns out with no stated reason. Fixing that gap now, as its own encounter, gives the later archiving encounter(s) a correct, already-consistent index to reason about instead of layering an archive-aware exception on top of a pre-existing hole — a cleaner split than discovering and fixing this mid-archive-design.

No schema change is needed for the same reason none was needed last time: `build-sqlite-fts5-encounter-index` deliberately made the table's columns generic (object_type/campaign/name/status/updated_on/body, none encounter-specific), and `add-world-lore-region-to-search-index` already proved the pattern extends cleanly to non-campaign-scoped types. Campaigns are actually the simplest of the four extensions so far: unlike lore's `enabled`→status mapping or world's singleton-with-fallback-name handling, a campaign already has a real `status` field in exactly the shape `_reindex_encounters` already reads it in, so `_reindex_campaigns` can copy that exact pattern rather than invent a new one.

The CLI/MCP surface needs no changes because both were already built generically: `cac index search --type` and `index_search`'s `object_type` parameter validate against `SEARCH_INDEX_OBJECT_TYPES`, not a hardcoded list, and `cac index status`/`index_status` iterate whatever keys `index_counts()` returns. This was true when world/lore/region were added and remains true here — confirmed by re-reading both files rather than assumed.

`clean-tests-and-lint` (world-assigned) applies directly: the Requirements above already calls out the specific existing tests that must be corrected rather than left to silently drift wrong once campaigns are indexed, and Verification below runs the full gate. `cli-mcp-parity` and `console-best-practices` (assigned to the `crypts-and-commits` region, which is where this change lives) do not newly apply: no CLI command or option is added or changed, and no new print/output call is introduced — the one existing `cac index search` print path already prints stored/derived fields with `markup=False`, and a campaign hit flows through that same generic path. `skills-authored-only-in-templates` and `workflow-doc-source-of-truth` are not implicated: no skill content or documented procedure changes, since this is purely an index-completeness fix with no new user-facing workflow step.

## Plan

1. **`core/config.py`**: add `SEARCH_INDEX_OBJECT_TYPE_CAMPAIGN = "campaign"`; extend `SEARCH_INDEX_OBJECT_TYPES` to `(SEARCH_INDEX_OBJECT_TYPE_ENCOUNTER, SEARCH_INDEX_OBJECT_TYPE_WORLD, SEARCH_INDEX_OBJECT_TYPE_LORE, SEARCH_INDEX_OBJECT_TYPE_REGION, SEARCH_INDEX_OBJECT_TYPE_CAMPAIGN)`.
2. **`core/search_index.py`**:
   - Import `campaign as campaign_core`, `CAMPAIGN_DIR_NAME`, and the new constant from `config`.
   - Add `_reindex_campaigns(root, conn) -> int`: for each `name` in `campaign_core.list_campaigns(root)`, `metadata, body = campaign_core.read_metadata(root, name)`; insert a row (`object_type="campaign"`, `campaign=""`, `name=name`, `status=metadata.get("status", "")`, `updated_on=metadata.get("updated_on", "")`, `body=body`); return the count.
   - Update `rebuild_index` to sum all five passes, adding `_reindex_campaigns(root, conn)`.
   - Update `_classify`: add a branch `if len(parts) == 2 and parts[0] == CAMPAIGN_DIR_NAME: return SEARCH_INDEX_OBJECT_TYPE_CAMPAIGN, "", path.stem`, placed alongside the existing lore/region branches; update the trailing comment/docstring that currently claims `campaigns/` paths are unindexed.
3. **Tests** (`tests/core/test_search_index.py`):
   - Correct every existing `count`/`index_counts()` assertion that becomes wrong once `_make_campaign` calls contribute an indexed row (going through each test in the file rather than a blanket search-and-replace, since some tests create one campaign and others two).
   - Rewrite `test_search_unknown_object_type_raises` to use a non-`"campaign"` invalid type string.
   - Rewrite (and rename) `test_delete_campaign_does_not_touch_index` to assert a deleted campaign's own row is removed from the index while its encounters' rows remain.
   - Add new tests mirroring the existing per-type shape: campaign indexing in `rebuild_index`/`index_counts`, a full-metadata search hit for a campaign, `object_type="campaign"` filtering, immediate post-create searchability, an indexed status reflecting a real transition (e.g. `campaign.open_campaign`) without a rebuild, and immediate post-delete removal.
4. **Tests** (`tests/cli/test_index.py`, `tests/mcp/test_index.py`): correct any count-based assertions affected by campaign fixtures now being indexed; add a `--type campaign` / `object_type="campaign"` coverage case in each, matching the existing per-type pattern already used for lore/region/world.

## Verification

- `pdm run pytest -q` passes, including all corrected and newly added tests above, with no skips or deletions used to dodge a failure.
- `pdm run ruff check .` reports zero errors and `pdm run ruff format .` reports no diffs.
- Manually run `cac index rebuild` against this repo's own `.sourcebook`, then `cac index status` — confirm the breakdown now includes a `campaign` count matching `cac campaign list`'s item count, alongside the existing `encounter`/`world`/`lore`/`region` counts.
- Manually run `cac index search --type campaign` for a phrase known to appear in a real campaign body in this repo (e.g. this very campaign's own body) and confirm a `campaign` hit is returned with the correct name/status/excerpt.

## Log

### Review - 2026-08-02T20:40:47Z - John Hoff

Reviewed against all five applicable lore items. clean-tests-and-lint, cli-mcp-parity, and console-best-practices are honored and independently verified against the current code (cli/index.py, mcp/index.py, core/search_index.py all confirmed to already be generic over object types, requiring no CLI/MCP or new-print-call changes). skills-authored-only-in-templates is correctly out of scope. workflow-doc-source-of-truth's outcome is correct - workflow.md's search-index section is generic enough that adding a campaign object type doesn't make it inaccurate - but the Plan's stated justification ("no new user-facing workflow step") isn't quite the lore's actual test ("would make an existing statement in workflow.md inaccurate"); worth tightening the Rationale's wording, though it isn't blocking. All of the Plan's factual claims about current search_index.py/config.py/campaign.py behavior and the two named test-fallout cases were independently verified as accurate. Approved to proceed.

### Completed - 2026-08-02T20:48:16Z - John Hoff

Verification passed: pdm run pytest -q (729 passed, no skips), ruff check . and ruff format . --check both clean. Manually rebuilt this repo's own .sourcebook (62 items: campaign 9, encounter 44, lore 5, region 3, world 1), campaign count matching cac campaign list's 9 entries. cac index search --type campaign for a phrase from this campaign's own body correctly returned it as a hit. Changes: SEARCH_INDEX_OBJECT_TYPE_CAMPAIGN added to core/config.py; _reindex_campaigns added and wired into rebuild_index, and _classify() taught to recognize campaigns/<name>.md in core/search_index.py, with the two now-stale "campaigns are unindexed" docstring/comments corrected; test fallout corrected across tests/core/test_search_index.py, tests/cli/test_index.py, and tests/mcp/test_index.py (count assertions fixed, the two tests asserting the old exclusion rewritten, new per-type coverage added). No CLI, MCP, or docs/workflow.md changes were needed.
