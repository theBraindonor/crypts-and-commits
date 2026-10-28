---
archived: false
campaign: c001-boss-edition
created_by: John Hoff
created_on: '2026-10-27T04:52:55Z'
depends_on:
- e001-finalize-boss-edition-design
kind: scripted
name: e004-add-world-branch-settings
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-10-27T05:02:14Z'
---

## Requirements

Implement the accepted world branch-settings contract in `docs/boss-edition.md`:
- `merge_target_branch` defaults to `main`.
- `planning_branch` defaults to `planning`.

Expose both settings through the world's existing metadata representation and through the world portion of prime, consistently across core, CLI, and MCP. A missing attribute uses its effective default without modifying an existing record, changing its audit stamps, or requiring bootstrap/migration. Absence, not truthiness, determines fallback; do not silently replace explicitly stored values.

Support explicit overrides through the existing `cac world set KEY VALUE` and `world_set(key, value)` interfaces. Preserve the existing generic string-value setter contract and unrelated metadata/body behavior. No new branch-name validation policy, Git ref syntax checks, branch-existence checks, current-branch detection, or branch-dependent lifecycle gates are introduced. The settings supply future skill guidance; endpoints do not create, switch, fetch, merge, or inspect branches.

Newly initialized worlds should record the two default attributes through the packaged world template. Existing worlds remain compatible when either or both attributes are absent. Returned World values after setters, body writes, and lore linking should expose the same effective metadata as ordinary reads; unrelated writes must not incidentally persist missing default attributes into older records.

Ship any necessary CLI/MCP exposure and documentation in this encounter. Retain existing tool/command names, arguments, budget behavior, and body input methods. Render user-provided setting values literally in touched CLI output, avoiding Rich markup interpretation.

This encounter does not implement branch workflow skills, boss records, numbering, campaign reactivation, or sourcebook migration. Keep schema version unchanged for these optional additive attributes. Do not edit this repository's managed world directly or run live bootstrap to adopt the settings; default reads work without adoption.

## Rationale

Later planning and campaign skills need configurable integration and planning branch names. The existing world setter already supports arbitrary metadata, but world reads currently return only persisted fields. Centralizing effective defaults in core prevents CLI, MCP, and prime from interpreting the same historical record differently, while preserving read-only behavior and backward compatibility.

This is the campaign's fourth tentative item, after design finalization, CLI body-file input, and narrower hook enforcement. The design encounter settled the names, defaults, and existing-interface approach.

## Plan

1. Read `docs/boss-edition.md` (branch configuration and e001 decision record), `CLAUDE.md`, and `AGENTS.md`. Work on `c001-boss-edition`. Use CodeGraph to inspect:
   - `packages/crypts-and-commits/src/cac/core/config.py` and `core/world.py`.
   - `packages/crypts-and-commits/src/cac/core/prime.py`.
   - `packages/crypts-and-commits/src/cac/cli/world.py` and `cli/prime.py`.
   - `packages/crypts-and-commits/src/cac/mcp/world.py` and `mcp/prime.py`.
   - Their corresponding tests under `packages/crypts-and-commits/tests/{core,cli,mcp}/`.
   Read the packaged `packages/crypts-and-commits/src/cac/core/templates/sourcebook/world.md`.
2. Define the two recognized keys/defaults in shared core configuration. Introduce or reuse a single core World-construction/projection helper that copies persisted metadata and fills missing defaults without mutating the loaded post. Apply it to ordinary reads and every operation returning a World, including generic attribute setters, body updates, and lore-link updates.
3. Keep write persistence separate from effective metadata. A setter explicitly stores the selected key/value through the current core write path and audit mechanism. Body/lore/unrelated metadata writes retain missing-setting state on disk unless that setting was explicitly set. Keep existing error and attribution behavior. Add the defaults to the new-world template; do not rewrite existing worlds or bump schema version.
4. Verify `assemble_prime` receives the same effective World through the core read path. Keep CLI/MCP wrappers thin; adjust them only as needed so `world get`, `world set`, `world_get`, `world_set`, `prime get`, and `prime_get` expose consistent values and preserve existing response shapes and budgets. Existing MCP operations provide parity; no new command/tool or Git-aware endpoint is needed.
5. Update touched CLI metadata/set output so freeform setting values are printed literally (`markup=False` for user/stored content), with CLI-authored labels/styling kept separate where useful. Preserve bracketed body output and e002's inline/file/editor body input behavior.
6. Add regression tests to `tests/core/test_world.py`, `tests/core/test_prime.py`, `tests/cli/test_world.py`, `tests/cli/test_prime.py`, `tests/mcp/test_world.py`, and `tests/mcp/test_prime.py` under `packages/crypts-and-commits/`. Cover legacy records missing both/one settings, overrides, missing-key-only fallback, new initialization, consistent return values across World-producing operations, byte/audit stability during reads, no incidental persistence during unrelated writes, and CLI/MCP/prime agreement. Use existing temporary-project fixtures; no live managed-record edits or bootstrap.
7. Update `packages/crypts-and-commits/src/cac/core/templates/docs/workflow.md` in the same change to define both settings, effective defaults versus persisted overrides, read-only fallback behavior, existing setter examples, and branch-agnostic endpoints. Add discoverable usage guidance to `docs/QUICKSTART.md`. Do not present future branch-management skills as shipped. No skill procedure change is required; leave deployed skills/hooks and local agent-instruction adoption to their existing workflows/later encounters.
8. Run the focused checks below, then full pytest and Ruff checks. Review the final diff, record verification through CAC, and obtain developer confirmation before marking complete.

## Verification

- First run `pdm run pytest packages/crypts-and-commits/tests/core/test_world.py packages/crypts-and-commits/tests/core/test_prime.py packages/crypts-and-commits/tests/cli/test_world.py packages/crypts-and-commits/tests/cli/test_prime.py packages/crypts-and-commits/tests/mcp/test_world.py packages/crypts-and-commits/tests/mcp/test_prime.py -q`.
- Confirm missing settings appear as main/planning in world and prime across all three surfaces. Confirm custom values (including branch names with slashes) survive setter/read round trips and are not replaced by defaults. Preserve explicit stored values rather than applying a truthiness fallback.
- For older records missing settings, snapshot record bytes/audit metadata before world/prime reads and assert they are unchanged afterward. Verify missing-world errors still work, and new-world initialization persists the template defaults.
- Verify every World-returning write gives effective settings without injecting missing defaults into persisted metadata during unrelated operations. Test explicit setting writes separately from unrelated metadata, body updates, and lore linking. Preserve body, unrelated frontmatter, assigned-lore behavior, and existing audit updates.
- Verify literal user-value output, CLI/MCP parity, prime response structure, existing budget/truncation behavior, and e002 body-input regressions. Confirm these endpoints do not add Git branch commands or gate behavior on the current branch.
- Inspect workflow/Quickstart documentation for accurate setting names, defaults, setter examples, read-only compatibility, and the separation between stored settings and future skill guidance.
- Run `pdm run pytest -q`, `pdm run ruff check .`, and `pdm run ruff format .` from the repository root; require passing tests and clean lint/formatting without skips, weakened/deleted tests, or suppressions to evade failures. Preserve unrelated user changes.
- Run `git diff --check` and review code/tests/docs for scope. Report verification and any limitations, and obtain developer confirmation before completion.

## Log

### Review - 2026-10-27T04:55:28Z - John Hoff

Independent review: PASS-WITH-NOTES. The scripted plan honors all five applicable lore entries: it requires full pytest and clean Ruff without evasions, preserves CLI/MCP parity and response budgets through thin wrappers, renders user/stored setting values literally, excludes deployed skill edits and live bootstrap, and updates the canonical workflow document in the same change. The settings contract agrees with the cited Boss Edition design and clearly separates effective defaults from persistence, including legacy reads and World-returning writes. No lore conflicts or flagged-but-unverified concerns were found; implementation and verification remain future work.

### Opened - 2026-10-27T04:57:47Z - John Hoff

Developer approved implementation after independent review.

### Message - 2026-10-27T05:01:54Z - John Hoff

Implementation and verification complete, pending developer confirmation. Added shared WORLD_BRANCH_DEFAULTS and a core World projection helper used by reads and every World-returning write. Missing branch keys expose main/planning in returned metadata only; legacy record reads preserve bytes/mtime/audit fields and unrelated writes do not backfill defaults. Explicit values, including falsey/malformed historical values, remain untouched. New-world template persists both defaults. Existing CLI/MCP world setters and prime paths expose the same effective values without new tools, Git commands, branch validation, or schema changes. Updated touched CLI metadata/set printing to preserve literal user values; added CLI help and workflow/Quickstart documentation. Added a shared legacy-world test fixture and 27 regression cases across core/CLI/MCP world and prime. Verification: 112 focused tests passed; full suite 1012 passed; Ruff check clean; Ruff format left 226 files unchanged; git diff --check clean; final code/test/docs diffs reviewed. Existing MCP wrappers need no code change because they already delegate to these core World-returning paths. No live managed-world adoption, bootstrap, or deployed artifact changes. Encounter remains open and changes uncommitted.

### Completed - 2026-10-27T05:02:14Z - John Hoff

Completed with explicit developer confirmation. Implemented effective merge_target_branch=main and planning_branch=planning defaults in shared core World projection, preserving explicit values and avoiding read-time writes or incidental persistence. New-world template records defaults; existing CLI/MCP setters and prime paths expose consistent effective metadata. Updated literal-safe CLI rendering, help, workflow reference, Quickstart, and 27 regression cases. Verification: 112 focused tests passed; all 1012 tests passed; Ruff check clean; Ruff format left 226 files unchanged; git diff --check clean; final diffs reviewed. No schema migration, live bootstrap, managed-world adoption, or deployed artifact changes. Changes remain uncommitted.
