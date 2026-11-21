---
archived: false
campaign: c004-tool-description-accuracy
created_by: John Hoff
created_on: '2026-11-21T05:54:32Z'
depends_on: []
kind: scripted
name: e001-index-search-description
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-11-21T06:03:42Z'
---

## Requirements

Make the `index_search` MCP tool description and the `cac index search` CLI help accurately describe what the search index covers, consistent with the Search index section of `packages/crypts-and-commits/src/cac/core/templates/docs/tool-reference.md` (lines ~536-558):

1. Name every searchable `object_type` value — exactly the members of `SEARCH_INDEX_OBJECT_TYPES` in `src/cac/core/config.py`: `world`, `lore`, `region`, `boss`, `campaign`, `encounter`, `rumor`, `ruling`.
2. State what text each type indexes, matching the implementation in `src/cac/core/search_index.py` (`sync_write`, `_rumor_text`, `_ruling_text`): world/lore/region/campaign/encounter index their body; boss indexes summary and body; rumor indexes summary, origin and body; ruling indexes summary, origin, `resolution` narrative and body.
3. State that every status is searchable and that archived records (of any archivable type, not only campaigns/encounters/bosses) are excluded unless `include_archived` / `--include-archived` is set.
4. Keep the existing missing/stale/rebuild-is-developer-only wording on the MCP description.
5. Add a drift-guard test so a future type added to `SEARCH_INDEX_OBJECT_TYPES` without updating both descriptions fails the suite. This settles b004's open question in favor of a test.

No behavior changes: the search algorithm, parameters, results and error messages stay as they are.

## Rationale

`index_search` currently says only "Boss summary/body is searchable." An agent reading only the tool description cannot discover that rumors (since e023) and rulings (since c002) are searchable, or that `object_type="rumor"` / `"ruling"` exist (originally raised as r003, promoted to b004). The CLI `--include-archived` help also names only "campaigns/encounters/bosses", although rumors and rulings archive too. `tool-reference.md` is already correct, so this encounter brings the two agent-facing surfaces into line with it, as `cli-mcp-parity` requires. The drift-guard test is what keeps this from regressing the next time a type is indexed.

## Plan

All paths are under `packages/crypts-and-commits/`.

1. **`src/cac/mcp/index.py` — `index_search` docstring.** Replace the "Boss summary/body is searchable. Archives are excluded unless requested." sentences with text that (a) lists the `object_type` filter values `world, lore, region, boss, campaign, encounter, rumor, ruling` (omit for all), (b) states the indexed text per type as in Requirement 2, and (c) states that every status is searchable and archived records are excluded unless `include_archived`. Keep the missing/stale/developer-only rebuild sentences. Keep it compact; the docstring is the MCP tool description sent to agents.
2. **`src/cac/cli/index.py` — `search` command.**
   - `--type/-t` help: list the same eight values (default all types).
   - `--include-archived` help: "Also include archived records (any type), excluded by default."
   - Command docstring: add a sentence summarizing indexed text per type, matching step 1, so `cac index search --help` carries the same information as the MCP description.
3. **`src/cac/core/search_index.py` — `search` docstring only.** Correct "Archived campaigns/encounters are excluded by default" to "Archived records are excluded by default". Docstring-only; no code change.
4. **Cross-check `tool-reference.md`.** Confirm that the Search index section matches the new descriptions. Change it only if a factual mismatch is found; none is expected.
5. **Drift-guard tests.**
   - `tests/mcp/test_index.py`: a test that asserts every value in `config.SEARCH_INDEX_OBJECT_TYPES` appears in `mcp_index.index_search.__doc__`, using a word-boundary regex so the check isn't satisfied by a substring.
   - `tests/cli/test_index.py`: a test that invokes `cac index search --help` and asserts every value in `config.SEARCH_INDEX_OBJECT_TYPES` appears in the output.
6. Run `pdm run pytest -q`, `pdm run ruff check .` and `pdm run ruff format .`, and fix anything they report.

## Verification

- `mcp_index.index_search.__doc__` and `cac index search --help` both name all eight object types and the per-type indexed text, and describe archive exclusion generically. Check this by reading the docstring and running `pdm run cac index search --help`.
- The new drift-guard tests pass, and fail when a temporary extra value is monkeypatched into `SEARCH_INDEX_OBJECT_TYPES` (a quick manual sanity check, not committed).
- `tool-reference.md` Search index section agrees with both descriptions.
- `git diff` shows docstring/help-text and test changes only. No logic changes in `core/`, `mcp/` or `cli/`.
- `pdm run pytest -q` passes; `pdm run ruff check .` reports zero errors; `pdm run ruff format .` produces no diffs (`clean-tests-and-lint`).

## Log

### Review - 2026-11-21T05:56:35Z - John Hoff

Independent lore review: PASS-WITH-NOTES. The Plan's facts match the cited code: the 8 SEARCH_INDEX_OBJECT_TYPES members; boss summary+body, rumor summary+origin+body, ruling summary+origin+resolution+body; and the outdated "Boss summary/body" and "campaigns/encounters/bosses" wording in `mcp/index.py`, `cli/index.py` and `core/search_index.py`. clean-tests-and-lint is honored: pytest, ruff check and ruff format are gated in step 6 and Verification. cli-mcp-parity is honored: no command change, both agent-facing surfaces are brought into line, and each gets its own drift guard. console-best-practices does not apply beyond help text, and skills-authored-only-in-templates does not apply. workflow-doc-source-of-truth is honored: tool-reference.md owns the contract, is already correct, and step 4 cross-checks it with an explicit justification for leaving it unchanged; there is no procedural change, so the phase guides stay untouched. Notes: (1) the new descriptions will say world/lore/region/campaign/encounter index their body, which tool-reference.md does not; step 4 should decide whether to add that clause so the owning doc stays at least as specific; (2) the drift guard covers type names only, not per-type indexed text; (3) avoid `[...]` in Typer help because rich renders it as markup. Not verified and possibly out of scope: other docs or skill templates that may repeat the outdated search wording.

### Opened - 2026-11-21T05:57:21Z - John Hoff

Opened with developer approval, including adding the per-type body clause to tool-reference.md (review note 1).

### Message - 2026-11-21T05:57:30Z - John Hoff

Deviation from Plan step 4, approved by the developer (ruling c004-e001-drift-guard-and-reference-specificity): tool-reference.md's Search index section gains the clause that world, lore, region, campaign and encounter records index their body, so the owning doc is at least as specific as the new descriptions. Help text will avoid [...] brackets (review note 3).

### Completed - 2026-11-21T06:03:42Z - John Hoff

Verification passed, confirmed by the developer. The index_search MCP description and cac index search help now name all 8 object types, the text each indexes, and generic archive exclusion. The core search docstring is corrected, and tool-reference.md gains the body clause (per ruling c004-e001-drift-guard-and-reference-specificity). Both drift guards pass and failed in a scratch check with an extra type. Full suite: 1724 passed; ruff check and ruff format --check are clean. The diff is docstrings, help text, one doc clause and tests only.
