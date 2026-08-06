---
archived: false
campaign: v0.1.7-rag-demo-application
created_by: John Hoff
created_on: '2026-08-06T18:02:17Z'
depends_on:
- add-campaign-and-encounter-lookup-tools
name: add-world-region-lore-search-tools
regions:
- demo-api
status: completed
updated_by: John Hoff
updated_on: '2026-08-06T21:51:40Z'
---

## Requirements

- The demo-api chat agent must be able to call tools that: get the world summary; list and get regions; list and get lore entries; and search the sourcebook index by phrase - all backed directly by `cac.core.world` / `cac.core.region` / `cac.core.lore` / `cac.core.search_index`, never a `cac` CLI subprocess or the MCP server (per the `demo-api-uses-cac-core-directly` region lore).
- Tools stay strictly read-only against `.sourcebook`: only non-mutating `core` functions are exposed (`read_world`, `list_regions`/`read_region`/`read_metadata`, `list_lore`/`read_lore`/`read_metadata`, `search`); no mutating call (including `rebuild_index`) is wrapped or ever invoked by a tool.
- Each new domain follows the existing `tools/` package shape established by `add-campaign-and-encounter-lookup-tools`: one module per domain exporting `build_tools(root) -> list[BaseTool]`, registered in `tools/__init__.py`'s `_BUILDERS` list - no change to the encounters/campaigns modules or to `graph.py`'s wiring.
- The search tool must clearly distinguish "index not built yet" from "built but zero matches" for the model, since `cac.core.search_index.search` returns `None` for the former and `[]` for the latter - collapsing that distinction would make the agent report "no results" when the real answer is "no index exists yet."
- Existing chat behavior and the already-shipped campaign/encounter tools keep working unchanged.

## Rationale

This is the direct follow-up to `add-campaign-and-encounter-lookup-tools`, extending the same `demo_api/chat/tools/` registry pattern to the remaining read-only `cac.core` domains the chat agent should be able to answer questions about: world context, regions, lore, and full-text search over indexed content. Nothing new needs to be designed here - the package shape (`build_tools(root)` closures aggregated by `_BUILDERS`), the `demo-api-uses-cac-core-directly` lore compliance, and the `ToolNode`/`tools_condition` wiring in `graph.py` all already exist and need no changes; this encounter only adds sibling modules and registers them, which is exactly the extension point the prior encounter's design was built to make cheap.

Two domains need a small departure from the "return the dataclass fields" pattern used for encounters/campaigns:
- `cac.core.region.Region` (`name`, `path`, `body`) and `cac.core.lore.Lore` (`name`, `body`) are thinner than what makes a useful chat answer - notably missing `assigned_lore` (region) and `enabled`/`assigned_to_world`/`assigned_regions` (lore), which only exist in the stored frontmatter. `get_region`/`get_lore` read that frontmatter directly via each module's `read_metadata(root, name)` instead of the dataclass, matching the richness `get_campaign`/`get_encounter` already got for free from their fuller dataclasses.
- `cac.core.search_index.search` returns `None` (index never built) vs. `[]` (built, no match) vs. a populated list - a real three-state result the tool must preserve rather than collapsing to always-a-list, so the model can tell a user "the search index hasn't been built yet" instead of falsely reporting no matches. The tool returns a small envelope dict (`{"available": bool, "hits": [...]}`) rather than a bare list, for exactly this reason.

The search tool intentionally exposes only `phrase`, `object_type`, `limit`, and `include_archived` - not `offset`/`snippet_tokens`, which are pagination/formatting knobs a chat agent has no reason to control itself; they're left at `cac.core.search_index`'s own defaults.

## Plan

1. Add four new modules to `packages/demo-api/src/demo_api/chat/tools/`, each `build_tools(root: Path) -> list[BaseTool]`:
   - `world.py`: `get_world()` - calls `cac.core.world.read_world(root)`, returns `{"name": metadata.get("name"), "assigned_lore": metadata.get("assigned_lore", []), "body": ...}`.
   - `region.py`: `list_regions()` - wraps `cac.core.region.list_regions`; `get_region(name: str)` - wraps `cac.core.region.read_metadata(root, name)`, returns `{"name", "path", "assigned_lore", "body"}` (using `region_core.ASSIGNED_LORE_KEY` for the metadata key, not a hardcoded string).
   - `lore.py`: `list_lore()` - wraps `cac.core.lore.list_lore`; `get_lore(name: str)` - wraps `cac.core.lore.read_metadata(root, name)`, returns `{"name", "enabled", "assigned_to_world", "assigned_regions", "body"}` (using `lore_core.ASSIGNED_REGIONS_KEY` for the metadata key).
   - `search.py`: `search_sourcebook(phrase: str, object_type: str | None = None, limit: int = 10, include_archived: bool = False)` - calls `cac.core.search_index.search(root, phrase, object_type=object_type, limit=limit, include_archived=include_archived)`; if the result is `None`, returns `{"available": False, "hits": []}`; otherwise `{"available": True, "hits": [<hit dict per SearchHit field>, ...]}`. The docstring lists the five valid `object_type` values (`encounter`, `campaign`, `lore`, `region`, `world`) and notes `phrase`/`object_type`/`limit` validation errors (`EmptySearchPhraseError`, `InvalidSearchQueryError`) propagate unchanged, same as the existing encounter/campaign tools' error-propagation approach.
2. Update `packages/demo-api/src/demo_api/chat/tools/__init__.py`: add `lore`, `region`, `search`, `world` to the `_BUILDERS` list (alongside the existing `campaigns`, `encounters`).
3. Tests, extending `packages/demo-api/tests/test_tools.py` with the same `tmp_path` + direct `cac.core` setup pattern already used there:
   - World: `cac.core.world.initialize_world(tmp_path)`, then assert `get_world` returns the templated name/body and an empty `assigned_lore`.
   - Region: `cac.core.lore.create_lore` + `cac.core.region.create_region` + `cac.core.region.assign_lore` to cover `list_regions`/`get_region` including a populated `assigned_lore`, plus a not-found case (`RegionNotFoundError`).
   - Lore: `cac.core.lore.create_lore`, then `set_enabled(False)` / `set_assigned_to_world(True)` / `add_assigned_region(...)` to cover `list_lore`/`get_lore` reflecting all four frontmatter fields, plus a not-found case (`LoreNotFoundError`).
   - Search: one test with no `rebuild_index` call asserting `search_sourcebook` returns `{"available": False, "hits": []}`; one test that creates a lore entry, calls `cac.core.search_index.rebuild_index(tmp_path)` directly (test setup only - the tool itself never calls it), then asserts a matching phrase returns `available: True` with a hit for that entry, and an `object_type` filter excludes non-matching types; one test asserting an empty phrase raises `EmptySearchPhraseError` unchanged.
   - Extend the existing `test_build_tools_aggregates_every_domain` assertion to include all ten tool names: the four existing (`list_campaigns`, `get_campaign`, `list_encounters`, `get_encounter`) plus six new (`get_world`, `list_regions`, `get_region`, `list_lore`, `get_lore`, `search_sourcebook`).

## Verification

- `pdm run pytest packages/demo-api -q` and the full `pdm run pytest -q` both pass.
- `pdm run ruff check .` reports zero errors and `pdm run ruff format .` reports no diffs.
- Manually start the demo-api server and send `/chat` messages exercising each new tool (e.g. "what regions exist in this project?", "search the sourcebook for X") to confirm real tool-call round trips; best-effort given this region's noted OpenRouter free-tier rate-limit flakiness, not a hard blocker.

## Log

### Review - 2026-08-06T18:11:06Z - John Hoff

Reviewed against both applicable lore items - clean-tests-and-lint (world) and demo-api-uses-cac-core-directly (demo-api region) - and the Plan honors both without gap: Verification correctly gates on pdm run pytest -q plus clean ruff check/ruff format, and every new tool is scoped to direct, non-mutating cac.core.world/region/lore/search_index calls, with an explicit, correct call-out that rebuild_index must never be invoked by a tool (test-only). All cac.core functions, constants, and exception classes the Plan cites (read_world, region.read_metadata/ASSIGNED_LORE_KEY/assign_lore, lore.read_metadata/ASSIGNED_REGIONS_KEY/set_enabled/set_assigned_to_world/add_assigned_region, search_index.search/SearchHit/EmptySearchPhraseError/InvalidSearchQueryError) were verified to exist with the signatures and three-state search-result behavior described, and the two target files (tools/__init__.py, tests/test_tools.py) match the existing _BUILDERS/build_tools(root) pattern the Plan extends. No conflicts or unverifiable gaps found; approved to proceed.

### Completed - 2026-08-06T21:51:40Z - John Hoff

Implemented and verified: four new demo_api/chat/tools/ modules (world.py, region.py, lore.py, search.py) wrap cac.core.world/region/lore/search_index read-only functions as LangChain tools, registered in tools/__init__.py's _BUILDERS list alongside the existing campaigns/encounters modules - no changes to graph.py wiring were needed. get_region/get_lore pull from read_metadata() to surface assigned_lore/enabled/assigned_to_world/assigned_regions fields the thinner dataclasses omit. search_sourcebook preserves the index-not-built (None) vs. zero-matches ([]) distinction as an {"available", "hits"} envelope. Extended tests/test_tools.py with coverage for all four domains including not-found and empty-phrase error propagation. Full suite (791 tests) passes, ruff clean, and live /chat smoke tests against a running server confirmed real tool round trips: list_regions/get_region correctly reported the real region path, and search_sourcebook's results matched a direct cac.core.search_index.search() call exactly (one real hit in an encounter, correctly reported as zero lore matches for a lore-scoped query).
