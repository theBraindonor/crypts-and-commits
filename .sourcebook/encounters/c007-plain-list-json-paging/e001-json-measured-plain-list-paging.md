---
archived: false
campaign: c007-plain-list-json-paging
created_by: John Hoff
created_on: '2026-11-23T21:01:57Z'
depends_on: []
kind: scripted
name: e001-json-measured-plain-list-paging
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-11-23T21:51:37Z'
---

## Requirements

Vanquish b009-json-measured-plain-list-paging. Every page from `lore_list`, `region_list` and `docs_list`, MCP and CLI, must be sized from the compact JSON the MCP tool returns, with its envelope reserved, so that:

1. Every MCP page from these lists, serialized as compact JSON (`references.encoded` / `budget._encoded`), fits `config.RESPONSE_BUDGET` including its `{items, next_cursor}` envelope, unless a single item alone exceeds the budget. That item still gets its own page so paging never stalls.
2. CLI and MCP page boundaries match exactly for the same inventory and cursor.
3. One generalized core helper does this. `core/prime.py::page_applicable_lore` is re-pointed at it with no behavior change, so there is no per-list helper.
4. The remaining paged lists are inventoried against this contract: the identity-bearing lists via `references.identity_page` (`boss_list`, `campaign_list`, `encounter_list`, `rumor_list`, `ruling_list`), `boss_candidates` and `index_search`. Each is either confirmed already JSON-measured with its envelope reserved, or brought under the helper if the change is small and same-shaped. Anything larger is captured as a rumor, not added to scope.
5. `templates/docs/tool-reference.md`'s budget contract states that plain lists are measured as compact JSON with their envelope reserved.
6. `pdm run pytest -q` passes and ruff is clean (`ruff check .`, `ruff format .`).

## Rationale

`core/budget.py::paginate` measures `len(render(item)) + 1` per item against the full budget. `lore_list` and `region_list` use the default `str` render. `docs_list` renders `name + summary`. Both ignore JSON quoting and escaping, the `{"name":…,"summary":…}` keys and the envelope, so an MCP page can exceed the response budget and break at different items than the CLI would. c006 fixed this for `prime_applicable_lore` with a compact-JSON, envelope-reserving wrapper (ruling c006-e001-json-measured-applicable-lore-paging). That ruling flagged the plain lists as a follow-up (r008 → b009), and `cli-mcp-parity` now carries the paging rule. One generalized helper keeps a single measurement rule for every list.

## Plan

1. **Core helper (`packages/crypts-and-commits/src/cac/core/budget.py`).** Add `json_page(items, cursor, *, project=lambda item: item, envelope=None, budget=None) -> Page`:
   - `project(item)` is the exact JSON value MCP returns for that item.
   - The envelope reserve is `len(_encoded({"items": [], "next_cursor": str(len(items)), **(envelope or {})}))`. This is the worst-case `next_cursor` digit count, matching `page_applicable_lore`'s reserve.
   - Items are measured as `len(_encoded(project(item)))` plus the existing `+1` separator, via `paginate(..., render=..., budget=budget - reserve)`, so cursor parsing, `InvalidCursorError` and the always-at-least-one-item rule are inherited unchanged.
   - `page.items` stay the original items (callers project for output), so the CLI keeps typed access.
2. **Re-point applicable lore (`core/prime.py`).** `page_applicable_lore` calls `budget.json_page(entries, cursor, project=applicable_lore_item, envelope={"identity": identity} if identity is not None else None)`. Page boundaries and every existing `test_prime` assertion stay unchanged.
3. **Core list pagers.** Add thin core helpers so both surfaces share one call:
   - `core/lore.py::page_lore(root, cursor)` → `budget.json_page(list_lore(root), cursor)` (items are name strings).
   - `core/region.py::page_regions(root, cursor)` → the same for `list_regions(root)`.
   - `core/docs.py::page_docs(cursor)` → `budget.json_page([{"name": n, "summary": s} for n, s in list_docs()], cursor)`. The items are the exact dicts MCP returns. Docs use the normal `RESPONSE_BUDGET` for lists (`DOCS_RESPONSE_BUDGET` stays scoped to `docs_get` bodies).
4. **Wrappers (thin only).**
   - `mcp/lore.py::lore_list`, `mcp/region.py::region_list` and `mcp/docs.py::docs_list` call the core pager and return `{"items": page.items, "next_cursor": page.next_cursor}`, which has the same shape as today.
   - `cli/lore.py`, `cli/region.py` and `cli/docs.py` `list` commands call the same core pager. Output formatting is unchanged, including the "No … found" empty-state messages and the dim `--cursor` hint. Per `console-best-practices`, stored content stays printed with `markup=False`, and docs' bold name markup stays as today.
5. **Inventory (Requirement 4).** Read `references.identity_page`, `boss_candidates` paging and `search_index.bounded_response`. Each list that already measures compact JSON with its envelope reserved is recorded as compliant via `encounter_record_message`. A small same-shaped gap is fixed onto `json_page` in this encounter and logged. A larger gap is captured as a rumor `rNNN-…` (number allocated from every `rumor_list(include_archived=True)` page) and logged.
6. **Docs.** In `packages/crypts-and-commits/src/cac/core/templates/docs/tool-reference.md`, extend the paged-list budget paragraph (around the "Paged lists (`*_list`, `boss_candidates`, `docs_list`, `prime_applicable_lore`)" text) to say that plain lists (`lore_list`, `region_list`, `docs_list`) measure each item's compact JSON with the `{items, next_cursor}` envelope reserved, the same as applicable lore, and that CLI pages break at the same items. Also adjust the `docs_list` section if it implies otherwise. No skill template or phase-workflow change is expected, since procedure is unchanged. If one turns out to be needed, update the owning `planning-workflow.md`/`development-workflow.md` per `workflow-doc-source-of-truth` and both skill flavors in `templates/skills/{claude,codex}/` per `skills-authored-only-in-templates`. Deployed `.claude/skills`/`.agents/skills` copies are never edited.
7. **Tests (mirroring `src/cac/`).**
   - `tests/core/test_budget.py`: `json_page` reserves the envelope (an inventory sized so the str-render would fit one more item than JSON allows), handles escaping (names/summaries with quotes, backslashes and non-ASCII under `ensure_ascii=False`), continues cursors, rejects invalid cursors, and gives an oversized single item its own page.
   - `tests/core/test_lore.py`, `test_region.py`, `test_docs.py`: the pagers return original items with JSON-measured boundaries under a monkeypatched small `RESPONSE_BUDGET`.
   - `tests/mcp/test_lore.py`, `test_region.py`, `test_docs.py`: each page `len(encoded(result)) <= RESPONSE_BUDGET` across a multi-page walk under a small budget, and the walk reassembles the full list.
   - `tests/cli/test_lore.py`, `test_region.py`, `test_docs.py`: the CLI walk with `--cursor` yields the same per-page items and cursors as the MCP walk (parity).
   - The existing `tests/core/test_prime.py` / `tests/mcp/test_prime.py` / `tests/cli/test_prime.py` applicable-lore tests pass unmodified.

## Verification

- `pdm run pytest -q` passes with no skipped or deleted tests. New tests cover Requirements 1–3 for all three lists, and the applicable-lore tests pass unmodified.
- `pdm run ruff check .` reports zero errors and `pdm run ruff format .` produces no diffs.
- Manual check from the repo root: `pdm run cac lore list`, `pdm run cac region list` and `pdm run cac docs list` print the same items as before (single page at the default budget), and the MCP `lore_list`/`region_list`/`docs_list` results have the same shape as before.
- The inventory outcome for every list in Requirement 4 is recorded on this encounter, with any rumor captured named.
- The `tool-reference.md` diff covers the plain-list measurement rule.

## Log

### Review - 2026-11-23T21:03:22Z - John Hoff

Independent lore review: PASS-WITH-NOTES. clean-tests-and-lint is honored: Requirement 6 and Verification gate on pytest passing with no skips or deletions, plus ruff check and format clean. cli-mcp-parity is honored, and it is this encounter's purpose: lore_list, region_list and docs_list move onto one shared core helper, budget.json_page, used by both MCP and CLI. It measures each projected item's compact JSON with the {items, next_cursor} envelope (plus identity) reserved at the worst-case cursor width. It keeps paginate's cursor and oversized-single-item semantics. CLI/MCP page-boundary parity is tested, and page_applicable_lore is re-pointed with arithmetic-identical reserves so the prime tests stay unmodified. console-best-practices is honored (markup=False kept for stored content). workflow-doc-source-of-truth is honored: tool-reference.md's budget contract and docs_list section are updated, and no phase-guide change is explicitly justified because procedure is unchanged. skills-authored-only-in-templates is honored (no skill change expected; template-only path stated). Notes for execution: (a) any Requirement 4 inventory gap fixed in-encounter must ship with its own CLI/MCP parity tests and a tool-reference.md update in the same change, or be captured as a rumor instead; (b) confirm the phase workflow guides do not mirror the old paged-list budget wording, and update any mirror found; (c) json_page must resolve budget=None to RESPONSE_BUDGET before subtracting the envelope reserve.

### Opened - 2026-11-23T21:06:59Z - John Hoff

Developer approved opening after PASS-WITH-NOTES review.

### Message - 2026-11-23T21:17:41Z - John Hoff

Requirement 4 inventory (no code changes, no rumor needed):
- Identity-bearing lists (boss_list, campaign_list, encounter_list, rumor_list, ruling_list) via references.identity_page: compliant. It reserves the compact-JSON {items, identities, next_cursor} envelope at worst-case cursor width (minus separators) and measures each item+identity pair as compact JSON through paginate.
- boss_candidates (core/boss_candidates.py::candidates): compliant. It reserves the full result (counts, diagnostics, worst-case next_cursor) as compact JSON before paging, and measures each bounded item as compact JSON.
- index_search: not cursor-paged (max_results/skip). search_index.bounded_response checks the whole compact-JSON response against RESPONSE_BUDGET and errors rather than overrunning. Compliant for its shape.
Reviewer note (b): planning-workflow.md and development-workflow.md only mention docs_list's existence, and the world-manager skill templates say lists are "paged under the response budget". Neither mirrors the old measurement wording, so no phase-guide or skill change is needed. Reviewer note (c): json_page resolves budget=None to config.RESPONSE_BUDGET before subtracting the reserve (covered by test_json_page_uses_config_response_budget_by_default). Reviewer note (a): not triggered, because no inventory list changed.

### Completed - 2026-11-23T21:51:37Z - John Hoff

Verification passed; developer confirmed completion. pytest 1758 passed (15 new tests, applicable-lore tests unmodified); ruff check/format clean; CLI lore/region/docs list output unchanged at the default budget; MCP list shapes unchanged; new lore/region tests fail against the pre-change source. Inventory: identity_page lists, boss_candidates and index_search already compliant. tool-reference.md budget contract updated; no phase-guide or skill change needed.
