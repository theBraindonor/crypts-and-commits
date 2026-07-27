---
campaign: v0.1.2-encounter-indexing-and-search
created_by: John Hoff
created_on: '2026-07-27T04:01:58Z'
depends_on:
- add-created-updated-stamps-to-world-lore-region
name: add-world-lore-region-to-search-index
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-07-27T04:30:06Z'
---

## Requirements

- Extend the SQLite FTS5 search index (`core/search_index.py`) to also index world, lore, and region content, reversing `docs/encounter-search-design.md`'s original "Lore/region/world stay out of search entirely" call and `build-sqlite-fts5-encounter-index`'s Requirements note that this "is explicitly **not** decided here." `add-created-updated-stamps-to-world-lore-region`'s Rationale identified the missing precondition for revisiting it - `updated_on` existing on world/lore/region the way it already does on encounters - and that precondition is now satisfied.
- Three new `object_type` values: `world`, `lore`, `region`, added to `SEARCH_INDEX_OBJECT_TYPES` (currently just `(encounter,)`). No CLI changes are needed to make them usable: `cac index search --type` already validates against this list generically (not a hardcoded check), and `cac index status`'s per-type breakdown already iterates whatever keys `index_counts` returns.
- `rebuild_index` must, in addition to its existing encounter pass, index:
  - exactly one `world` row for the singleton `world.md`;
  - one `lore` row per name in `lore.list_lore`;
  - one `region` row per name in `region.list_regions`.
- Schema/column semantics for the three new types (no schema/DDL change - the existing columns already generalize):
  - `campaign` - empty string. The column means "the campaign an encounter belongs to"; world/lore/region are not scoped to a campaign, so leaving it unset is correct, not a gap.
  - `status` - `lore` reports its `enabled` flag as the string `"enabled"`/`"disabled"` (a real, filterable state). `world` and `region` have no natural status concept; leave the column as an empty string (renders as `[]` in `cac index search` output - acceptable since the column is already optional/UNINDEXED metadata, not a required label).
  - `name` - lore/region rows use their existing file-stem name, same as encounters today. The world row uses its frontmatter `name` attribute, falling back to the literal string `"world"` if unset (older bootstraps may predate that key).
  - `updated_on` - each object's own `updated_on` frontmatter field, all three now guaranteed to have one.
- Disabled lore is still indexed and searchable, just labeled `disabled` - consistent with how `completed`/`abandoned` encounters remain searchable today. Nothing is excluded from the index based on status.
- `docs/encounter-search-design.md`'s "Ownership" paragraph currently states lore/region/world "stay out of search entirely" as settled fact - that claim is now false and must be corrected in place (not left to silently mislead a future reader), noting the decision was revisited once the `updated_on` precondition existed.
- No MCP tool changes and no changes to `cli/index.py` - the existing CLI-only `status`/`rebuild`/`search` surface already generalizes over `object_type` without modification.

## Rationale

The two decisions this encounter closes were both explicitly left open by name in prior encounters, not invented here: `build-sqlite-fts5-encounter-index`'s Requirements said "Whether lore/region/world ever join search is explicitly not decided here," and `add-created-updated-stamps-to-world-lore-region`'s Rationale explained *why* it was adding `updated_on` to world/lore/region at all - because a "common index model" extending search to those objects "needs `updated_on` to already exist on those objects before that extension can be designed, the same way it already exists on encounters today." That precondition is done; this encounter is the extension it was building toward.

The schema needs no migration because `build-sqlite-fts5-encounter-index` already made the table's shape generic on purpose ("Schema must not be encounter-specific" - object_type/campaign/name/status/updated_on/body columns, none of which hardcode "encounter"). Only `SEARCH_INDEX_OBJECT_TYPES` (a plain config tuple) and `rebuild_index`'s reindex passes need to change; `search`, `index_counts`, and the CLI already operate generically over whatever `object_type` values exist in the table.

`campaign`/`status` being left empty for the new types (rather than inventing a placeholder value) mirrors how the table already tolerates optional/UNINDEXED metadata - `status` is not used in ranking or in the `MATCH` predicate, only displayed, so an empty string is a faithful "not applicable" rather than a hack. `lore`'s `enabled` flag is the one place a real status-like signal already exists on a non-encounter object, so it's surfaced rather than discarded.

Correcting `docs/encounter-search-design.md` is in scope, not incidental cleanup, because that doc is the design record for this exact feature area and currently states the opposite of what will be true after this encounter ships - leaving it uncorrected would actively mislead the next reader (agent or developer) who consults it before touching search.

`clean-tests-and-lint` (world-assigned) and `console-best-practices`/`cli-mcp-parity` (assigned to the `crypts-and-commits` region, which is where every code change in this encounter lives) apply. `console-best-practices` is already honored by the existing `cac index search` code path ( `markup=False` for stored/derived text) - this encounter adds no new print call. `cli-mcp-parity` is not implicated - no new CLI command or option is introduced, so there is no new CLI-without-MCP surface to justify.

## Plan

1. **`core/config.py`**: add `SEARCH_INDEX_OBJECT_TYPE_WORLD = "world"`, `SEARCH_INDEX_OBJECT_TYPE_LORE = "lore"`, `SEARCH_INDEX_OBJECT_TYPE_REGION = "region"`; extend `SEARCH_INDEX_OBJECT_TYPES` to `(SEARCH_INDEX_OBJECT_TYPE_ENCOUNTER, SEARCH_INDEX_OBJECT_TYPE_WORLD, SEARCH_INDEX_OBJECT_TYPE_LORE, SEARCH_INDEX_OBJECT_TYPE_REGION)`.
2. **`core/search_index.py`**:
   - Import `world as world_core`, `lore as lore_core`, `region as region_core`, and the three new constants from `config`.
   - Add `_reindex_world(root, conn) -> int`: call `world_core.read_world(root)`; on `world_core.WorldNotFoundError`, return `0` (defensive - mirrors how the encounter/campaign passes tolerate an absent directory rather than assuming bootstrap already happened). Otherwise insert one row (`object_type="world"`, `campaign=""`, `name=metadata.get("name") or "world"`, `status=""`, `updated_on=metadata.get("updated_on", "")`, `body=body`) and return `1`.
   - Add `_reindex_lore(root, conn) -> int`: for each `name` in `lore_core.list_lore(root)`, `metadata, body = lore_core.read_metadata(root, name)`; `status = "enabled" if metadata.get("enabled", True) else "disabled"`; insert a row (`object_type="lore"`, `campaign=""`, `name=name`, `status=status`, `updated_on=metadata.get("updated_on", "")`, `body=body`); return the count.
   - Add `_reindex_regions(root, conn) -> int`: for each `name` in `region_core.list_regions(root)`, `metadata, body = region_core.read_metadata(root, name)`; insert a row (`object_type="region"`, `campaign=""`, `name=name`, `status=""`, `updated_on=metadata.get("updated_on", "")`, `body=body`); return the count.
   - Update `rebuild_index` to sum all four passes: `count = _reindex_encounters(root, conn) + _reindex_world(root, conn) + _reindex_lore(root, conn) + _reindex_regions(root, conn)`.
3. **`docs/encounter-search-design.md`**: in the "Why this is a separate problem" section, replace the sentence "Lore/region/world stay out of search entirely." with a short correction noting this was revisited and reversed once `updated_on` existed on all three (naming this encounter), pointing at `core/search_index.py` as the current source of truth rather than restating implementation detail in the doc. Leave the rest of the doc's historical framing intact - it is explicitly "design notes," not something this encounter needs to fully rewrite.
4. **Tests**:
   - `tests/core/test_search_index.py`: extend the rebuild fixtures to include lore and region entries alongside encounters (world.md is already present in any bootstrapped test root). Add/extend assertions: `rebuild_index`'s returned count includes `1` world row + one row per lore/region entry in addition to encounters; `index_counts()` includes `world`, `lore`, `region` keys with correct values; `search()` finds a phrase unique to a lore body and returns a hit with the right `name`/`updated_on` and `status in {"enabled", "disabled"}` matching that entry's `enabled` flag; same for a region body (`status == ""`); same for the world body; `object_type="lore"`/`"region"`/`"world"` each filter correctly; a lore entry created with `enabled=False` is still returned by an unfiltered search but labeled `disabled`.
   - `tests/cli/test_index.py`: `cac index rebuild` / `cac index status` output reflects the new type counts; `cac index search --type lore` / `--type region` / `--type world` narrow results correctly; a region hit (empty status) renders its result line without crashing or printing a literal `None`.

## Verification

- `pdm run pytest -q` passes, including the new/updated tests above, with no skips or deletions used to dodge a failure.
- `pdm run ruff check .` reports zero errors and `pdm run ruff format .` reports no diffs.
- Manually run `cac index rebuild` against this repo's own `.sourcebook`, then `cac index status` - confirm the breakdown shows `world: 1`, `lore: N`, and `region: 3`, matching `cac lore list` (count) and `cac region list` (count), alongside the existing `encounter` count.
- Manually run `cac index search` for a distinctive phrase known to appear in a real lore body (e.g. from `clean-tests-and-lint`) and confirm a `lore` hit appears with a correct name/status/excerpt.
- Manually run `cac index search` for a phrase from an actual region body and confirm a `region` hit appears with an empty-but-non-crashing status segment.
- Manually run `cac index search --type world` for a phrase known to appear in `world.md`'s body and confirm the world row is returned.
- Confirm `docs/encounter-search-design.md` no longer states that lore/region/world stay out of search.

## Log

### Review - 2026-07-27T04:05:20Z - John Hoff

Reviewed against clean-tests-and-lint (world), cli-mcp-parity and console-best-practices (both assigned to the crypts-and-commits region). All three are honored: the Verification section satisfies the test/lint gate verbatim; the existing cac index search print path in cli/index.py already uses markup=False on all stored/derived fields and is generic over object_type, so no new markup handling is needed; and no cli/ file changes or new commands are introduced, so the literal CLI/MCP parity trigger doesn't fire. I verified the Plan's supporting technical claims directly against source (core/config.py, core/search_index.py, cli/index.py, docs/encounter-search-design.md) and they check out. One non-blocking note for the record: this encounter expands the functional surface of cac index status/rebuild/search (three new object types), and that command family has zero MCP tool equivalents today (a pre-existing gap, not created here) - the Plan doesn't flag this expansion against that gap, which is a defensible scope call but worth the GM's awareness going forward.

### Message - 2026-07-27T04:22:45Z - John Hoff

Post-review refinement, discovered while exercising the feature: cac index search's result line showed name/status/updated but not which object_type matched, which now matters because an unfiltered search mixes encounter/world/lore/region hits together (e.g. searching "no-verify" returns a lore hit and two encounter hits side by side with no visual way to tell them apart). Added the hit's object_type to the printed line - `#{rank}  {score:.3f}  [{object_type}] {name}  [{status}]  updated {updated_on}` - in cli/index.py only, with matching assertions added to tests/cli/test_index.py. This is a same-scope refinement of the already-approved "return a ranking of matching results" requirement (mirroring how add-index-search-command's Log recorded the analogous post-review addition of the score field), not a new capability - no core/config.py or search_index.py change, no lore-relevant behavior changed (still markup=False for stored/derived text). pdm run pytest -q (646 passed) and ruff check/format --check both clean after the change.

### Message - 2026-07-27T04:26:09Z - John Hoff

Second post-review refinement, same scope as the object_type addition above: added a static one-line legend/header ("RANK  SCORE   TYPE        NAME  STATUS  UPDATED") printed once above the result list in cac index search, per GM request after seeing that mixed-type result output was hard to parse without knowing what each field meant. This is a static, CLI-authored string with no stored/derived content, so it is printed with default markup=True (contains no brackets or user input) - console-best-practices' markup=False rule does not apply to it, same reasoning already used for the existing "[dim]More results..." hint. Considered and rejected a fully column-aligned table (computed per-page column widths): more code, edge cases around long names/excerpts breaking alignment, and more test surface, for a CLI-only output path - the GM confirmed the simple legend line is preferred. No core/config.py or search_index.py change; cli/index.py and tests/cli/test_index.py only. pdm run pytest -q (646 passed) and ruff check/format --check both clean after the change.

### Completed - 2026-07-27T04:30:06Z - John Hoff

Verification passed: pdm run pytest -q (646 passed, no skips), ruff check . and ruff format . --check both clean. Manually rebuilt this repo's own .sourcebook (37 items: encounter 30, lore 3, region 3, world 1, matching cac lore list/cac region list counts). Verified cac index search --type lore/region/world each return correct hits with name/status/excerpt, including the empty-status render for region/world. docs/encounter-search-design.md corrected to no longer claim lore/region/world stay out of search. Two post-review refinements recorded and verified: (1) result lines now show [object_type] so mixed-type search output is disambiguated, (2) a static header/legend line was added above results for the same reason.
