---
archived: false
campaign: c002-rulings
created_by: John Hoff
created_on: '2026-11-21T02:22:24Z'
depends_on:
- e001-ruling-records-core
kind: scripted
name: e002-ruling-search-index
regions:
- crypts-and-commits
status: reviewed
updated_by: John Hoff
updated_on: '2026-11-21T02:24:39Z'
---

## Requirements

Make rulings a searchable record type in the derived full-text index, per `b005-ruling-records`. Rulings shipped in e001 but are not classified, indexed or part of the freshness inventory.

- **Search type.** Add `ruling` as a search object type in `config.SEARCH_INDEX_OBJECT_TYPES`, via a new `SEARCH_INDEX_OBJECT_TYPE_RULING = "ruling"`. Then `index_search(object_type="ruling")` / `cac index search --type ruling` filter to rulings. Unknown-type validation and errors keep listing every valid type.
- **Classification.** `search_index._classify` maps `rulings/<name>.md` to `("ruling", "", name, False)` and `archive/rulings/<name>.md` to `("ruling", "", name, True)`. The identity is `(object_type, campaign, name)` with an empty `campaign`, like bosses and rumors, because ruling storage is flat and the campaign is already encoded in the canonical name. Live and archived locations share one identity, so archiving moves the row in place.
- **Indexed text.** Ruling rows index the summary, the free-text origin, the `resolution` narrative (empty while `recorded`), and the body. That way a planning session can find a ruling by the narrative of how it was canonized or noted. Status, `updated_on` and the archive flag fill the standard columns, and every status is searchable.
- **Rebuild.** `rebuild_index` reindexes all live and archived rulings through `ruling.list_rulings(include_archived=True)` and `ruling.read_metadata`, mirroring `_reindex_rumors`. The returned count includes them.
- **Incremental sync.** `sync_write` builds the same ruling text as rebuild, so the incremental and full paths produce identical rows. Create, update, canonize, note, reopen and archive all keep the index fresh. Because the classification is shared, `Recovery` captures and restores ruling rows and fingerprints automatically.
- **Freshness inventory.** `index_snapshot.inventory` enumerates `rulings/` and `archive/rulings/`. Then ruling files edited outside CAC, or missing from an index built before this change, make the index report stale. The snapshot format `VERSION` stays `"1"`. An older index with no ruling rows is still correct for a sourcebook with no rulings, and one that has rulings already fails the inventory comparison.
- **Docs, in the same change:**
  - `templates/docs/tool-reference.md` Search index section: add ruling to the covered and inventoried types, and describe the ruling hit text (summary, origin, resolution, body).
  - `templates/docs/workflow.md`: change the Rulings section's "not yet searchable or primed" to say rulings are searchable under their own type and not yet primed.
  - `tool-reference.md` Rulings section: remove the "not yet indexed for search" sentence.

## Rationale

`b005` requires that rulings be discoverable during planning triage, and full-text search is CAC's discovery surface for record text. Following the rumor indexing pattern (shared `_classify`, a `_reindex_*` helper, a dedicated text builder shared by rebuild and sync, and inventory directories) reuses reviewed code paths for incremental sync, `Recovery` and freshness. Ruling writes then get the same atomic row and fingerprint guarantees as every other record type.

Indexing the `resolution` narrative is the main value for planning. Canonization narratives describe which lore and regions changed, and that is what a later session searches for.

Keeping the snapshot `VERSION` unchanged avoids forcing a rebuild on sourcebooks that never recorded a ruling. Sourcebooks that have rulings correctly go stale and need the developer-only rebuild. That includes this repository, which now has two recorded rulings.

**Out of scope:**
- Prime exposure of recorded rulings (a later c002 encounter).
- Skill and procedure text.
- General accuracy of the `index_search` / `cac index search` descriptions and help text, which is b004's goal (from r003). This encounter adds no new type enumerations to those descriptions.

## Plan

1. **`core/config.py`:** add `SEARCH_INDEX_OBJECT_TYPE_RULING = "ruling"` and append it to `SEARCH_INDEX_OBJECT_TYPES`.
2. **`core/search_index.py`:**
   - Import `RULING_DIR_NAME` and the new type constant.
   - Add `_ruling_text(metadata, body)`, returning summary, origin, resolution (or empty) and body joined by blank lines.
   - Add `_reindex_rulings(root, conn)`, mirroring `_reindex_rumors`. It returns 0 when neither the live nor the archive directory exists. Add it to `rebuild_index`'s sum.
   - Add the two ruling branches to `_classify`.
   - In `sync_write`, use `_ruling_text` for the ruling type.
3. **`core/index_snapshot.py`:** add `config.RULING_DIR_NAME` and `f"{config.ARCHIVE_DIR_NAME}/{config.RULING_DIR_NAME}"` to the inventory directory list.
4. **Docs:** apply the `tool-reference.md` and `workflow.md` edits listed in Requirements. Keep `workflow.md` within the 45,000-character test cap.
5. **Tests:**
   - `tests/core/test_ruling.py`:
     - Replace the e001 index-isolation test with an index-integration test. With a built index, creating, updating, canonizing, reopening, noting and archiving a ruling keeps `status` fresh.
     - `search(..., object_type="ruling")` finds a ruling by a body term, a summary term, an origin term and a resolution term.
     - After archiving, the hit is excluded by default and returned with `include_archived=True` and `archived: true`.
     - `index_counts()["ruling"]` matches.
     - Rebuild after these writes produces the same counts as the incremental path.
   - Add a staleness test: a ruling file changed outside CAC, or a ruling present when the index was built without one, makes `status` report stale.
   - `tests/core/test_search_index.py`: add ruling `_classify` cases for live, archived and nested or unrelated paths returning `None`, plus a rebuild count, following the existing rumor tests.
   - Add a CLI or MCP index search test with `object_type="ruling"` (`--type ruling`) where existing index tests enumerate types.
   - Update any test that asserts the exact `SEARCH_INDEX_OBJECT_TYPES` tuple or the unknown-type error text.

## Verification

- `pdm run pytest -q` passes, with no skips or deletions added to dodge failures.
- `pdm run ruff check .` reports zero errors, and `pdm run ruff format --check .` reports no changes.
- A manual smoke test in a temporary scratch project. The world is seeded and the index is built through core Python (`world.initialize_world`, `search_index.rebuild_index`), never through the developer-only `cac bootstrap init` or `cac index rebuild` commands. The steps:
  1. Open a campaign and an encounter.
  2. Build the index.
  3. Create a ruling and confirm `cac index status` is fresh with a `ruling: 1` count.
  4. Search a body term with `--type ruling`.
  5. Canonize it with a distinctive narrative word and find it by that word.
  6. Archive it, then confirm it is hidden by default and shown with `--include-archived`.
  7. Edit the ruling file outside CAC and confirm `cac index status` reports stale.
- Docs describe exactly the shipped coverage and hit text, checked against the diff.
- After merge, this repository's index will be stale because two rulings exist and were never indexed. Recovery is the developer-run `cac index rebuild`. The assistant never runs it.

## Log

### Review - 2026-11-21T02:24:39Z - John Hoff

PASS-WITH-NOTES. The scripted plan is consistent with all 5 applicable lore items.
- **clean-tests-and-lint:** the Verification gates on pytest and ruff with no skips. Apply `ruff format .` rather than only `--check`.
- **cli-mcp-parity:** no commands are added. Ruling filtering reuses the shared `object_type` validation. Prefer covering both the CLI `--type ruling` and MCP `object_type="ruling"` search, or confirm they share core validation.
- **console-best-practices** and **skills-authored-only-in-templates:** not triggered.
- **workflow-doc-source-of-truth:** satisfied in the same change. The plan updates the `tool-reference.md` Search index and Rulings sections and `workflow.md`'s Rulings statement, keeps the 45,000-character cap, and justifies deferring help-text accuracy to b004.

Unverified notes for implementation:
- Update any other `tool-reference.md` list of valid object types or the unknown-type error text.
- Check that the CLI/MCP help does not list types inline without `ruling`.
- Confirm that `sync_write` moves a ruling's row in place on archive, as it does for rumors.
- Keep the smoke test's direct file edit and Python `rebuild_index` call strictly inside the temporary scratch project, never this repo's `.sourcebook`. After merge, the developer runs `cac index rebuild` to fix this repo's stale index.
