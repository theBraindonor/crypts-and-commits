---
archived: false
campaign: v0.1.8-release-readiness
created_by: John Hoff
created_on: '2026-08-05T02:51:26Z'
depends_on: []
name: review-unit-test-smells
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-08-09T04:48:09Z'
---

# Encounter

## Requirements

- Audit `packages/crypts-and-commits/tests/` for the cause(s) of the test suite's long run time, and fix what's found:
  - Add a shared `packages/crypts-and-commits/tests/conftest.py` providing the currently duplicated-per-file fixtures (`_use_tmp_cwd`, a default git-identity mock) and shared setup helpers (e.g. create/open a campaign), removing the copy-pasted versions from the individual test files.
  - Apply a default git-identity mock across `tests/cli/` (the one subtree that currently lacks it, unlike `tests/core/` and `tests/mcp/`), so real `git config user.name` subprocess spawns stop happening on every write-shaped CLI test.
  - Replace the CLI tests that invoke the full `cac bootstrap init` pipeline only to get a bare `.sourcebook/world.md` on disk (not to test bootstrap itself) with a lighter-weight seed helper built on the existing `core.bootstrap.initialize()` + `core.world.initialize_world()` primitives. Leave `tests/cli/test_bootstrap.py`'s own invocations untouched, since those are testing bootstrap behavior.
  - Narrow `tests/mcp/test_encounter.py`'s `_active_campaign` fixture from `autouse=True` to opt-in, since not every test in that file needs an open campaign.
  - Register a `pytest` marker (e.g. `integration`) and apply it to `tests/core/test_search_index.py`'s genuinely cross-module/real-sqlite tests, to make the distinction explicit for the future. Per explicit GM decision, this is a tag only — `addopts` is not changed, and `pdm run pytest -q` continues to run the full suite including these by default; nothing is excluded from the standard command the `clean-tests-and-lint` lore gates on.
- No test's assertions or behavioral coverage may change as a side effect of this cleanup — only setup/fixture mechanics move or get de-duplicated. Test count (804 as of the audit) should be unchanged unless a rename is involved.
- Restructuring is bounded to the smells actually found in the audit below; this is not a general permission to reorganize the test tree further.

## Rationale

A slow unit test suite discourages running it frequently during development and in CI, and often signals that "unit" tests have quietly become integration tests (e.g. hitting real disk I/O or spawning real subprocesses per test rather than using shared/lighter fixtures) — a bar the `clean-tests-and-lint` lore already gates every encounter's Verification against, so it's a natural clean-up target ahead of a public release.

An independent audit (recorded here) found the suite's ~72s runtime (804 tests) has no dominant outlier — the slowest single test is 1.21s — so the cost is systemic rather than a few slow tests to fix in isolation:

- **`tests/cli/` costs ~4x more per test than `tests/core/`** (37.3s/255 tests ≈ 146ms/test vs. 15.3s/441 tests ≈ 35ms/test), and the single largest concrete cause is that `tests/core/` and `tests/mcp/` both mock `git_utils.current_git_user` via an autouse fixture, but none of the 8 `tests/cli/` files do — so real `git config user.name` subprocess spawns (~19ms each on the audit machine) happen on all 400+ write-shaped `runner.invoke` calls in `cli/`, roughly 7-8s of the 37s `cli/` subtree spent on identity resolution the rest of the suite already solved.
- 65 tests invoke the full 7-stage `cac bootstrap init` pipeline (`.sourcebook` dir, `world.md`, MCP config, Claude settings, Codex config/hook, 18 packaged skill files); 44 of those (in `test_prime.py`, `test_index.py`, `test_world.py`, `test_lore.py`) only need `world.md` to exist and aren't testing bootstrap behavior at all.
- There is no `conftest.py` anywhere in the tree, so `_use_tmp_cwd` is byte-identically duplicated across 15 files, the git-identity mock across 11 files, and a `_break_git_identity` helper across 5 — all copy-paste, not deliberate per-file variation.
- `tests/core/test_search_index.py` is the one file that's genuinely integration-shaped (real sqlite3 + campaign/encounter wiring end-to-end, 5-10x the `core/` per-test average) — legitimate coverage, worth naming explicitly rather than leaving it structurally indistinguishable from the rest of `core/`.
- `tests/mcp/test_encounter.py`'s `_active_campaign` autouse fixture opens a campaign for every test in the file even when unneeded — a minor over-broad-fixture smell, called out for completeness though `mcp/` is already the cheapest subtree.
- No sleeps, polling, or fixable fixture-scope issues were found — every fixture is function-scoped by design, so scope-widening isn't an available lever here.

The GM has confirmed all of the above should be fixed within this same encounter rather than deferred as a recommendation-only follow-up, with one explicit scoping call: the new `integration` marker tags `test_search_index.py` for future selective runs but does not change what `pdm run pytest -q` covers by default.

## Plan

1. Create `packages/crypts-and-commits/tests/conftest.py` with:
   - An autouse `_use_tmp_cwd` fixture (`monkeypatch.chdir(tmp_path)`), replacing the identical copies in the 15 files that currently define it locally.
   - An autouse default git-identity mock (patching `cac.core.git_utils.current_git_user` to return a fixed name), replacing the copies in the 11 `core/`/`mcp/` files, and newly applying it to all 8 `tests/cli/` files (none of which mock it today).
   - A `seed_world(root)` helper wrapping `cac.core.bootstrap.initialize(root)` + `cac.core.world.initialize_world(root)` — the same lighter primitives `cli/bootstrap.py::init()` composes into its full 7-stage pipeline — for tests that just need a `.sourcebook/world.md` on disk.
   - Shared `create_campaign`/`open_campaign` helpers to replace the ad hoc re-typed setup sequences scattered across `cli/test_encounter.py`, `cli/test_lore.py`, `cli/test_region.py`, and others.
   - Keep `_break_git_identity` as a local override available to the small number of negative-path tests that need it (they override the conftest default within that test), rather than promoting it into conftest itself.
2. Delete the now-redundant per-file `_use_tmp_cwd` and git-identity-mock fixture definitions from the 15 + 11 files identified in the audit, confirming each file still passes using the shared conftest versions.
3. In `tests/cli/test_prime.py`, `test_index.py`, `test_world.py`, and `test_lore.py`, replace the 44 call sites that call `runner.invoke(app, ["bootstrap", "init"])` purely for setup with the new `seed_world()` helper. Leave `tests/cli/test_bootstrap.py` untouched.
4. In `tests/mcp/test_encounter.py`, change `_active_campaign` from `autouse=True` to a normal fixture, and add it explicitly to the tests that need an open campaign (identified by which currently rely on it passing).
5. Add an `integration` marker registration to root `pyproject.toml`'s `[tool.pytest.ini_options]` (`markers = [...]`), and apply `@pytest.mark.integration` to the cross-module/real-sqlite tests in `tests/core/test_search_index.py`. Do not touch `addopts` — the marker is informational only.
6. Run the full suite and lint gate (see Verification) and fix anything that regresses before considering this encounter's work done.

## Verification

- `pdm run pytest -q` passes with the same test count as the pre-change baseline (804, allowing only for any intentional rename), no skips, no deletions to dodge failures.
- `pdm run pytest -q --durations=30` shows the long tail is gone from `tests/cli/` specifically — no expectation of a specific target number (environment-dependent), but the aggregate suite time and the `cli/`-subtree-vs-`core/`-subtree per-test-cost gap noted in the audit should both visibly shrink compared to the recorded baseline (72.30s full run; 146ms/test in `cli/` vs. 35ms/test in `core/`).
- `pdm run ruff check .` reports zero errors and `pdm run ruff format .` reports no diffs, per the `clean-tests-and-lint` lore gate.
- Spot-check a sample of touched test files to confirm only fixture/setup mechanics changed — no test assertions or coverage were altered as a side effect.
- Confirm `pdm run pytest -q` (no `-m` filter) still includes `tests/core/test_search_index.py`'s newly-marked tests, per the explicit GM decision not to exclude them from the default run.

## Log

### Review - 2026-08-09T03:21:02Z - John Hoff

Reviewed against all five applicable lore items. `clean-tests-and-lint` is directly and correctly honored: the Plan and Verification require the full `pdm run pytest -q` (804 tests, no skips) and clean `ruff check`/`format` gates, and the new `integration` marker is explicitly scoped as informational-only with `addopts` untouched, preserving the default-run coverage the lore protects. `cli-mcp-parity`, `console-best-practices`, `skills-authored-only-in-templates`, and `workflow-doc-source-of-truth` are all region-assigned but not triggered — this encounter's scope is confined to `tests/**` fixture/setup mechanics and a `pyproject.toml` marker registration, with no `cli/`, `mcp/`, `core/*.py` logic, or skill-template changes. The Plan is internally consistent with its own audit data and includes an explicit no-coverage-change constraint plus a spot-check verification step. One non-blocking note: the audit's specific per-file counts (15/11/8/44) aren't individually enumerated in the encounter body and weren't independently verified here, but the Plan's own spot-check step is the right place to confirm them during execution, not at review time.

### Message - 2026-08-09T03:52:29Z - John Hoff

Implementation complete; verified independently (804 passed in 25.44s vs. 72.30s baseline, ~65% faster; `pdm run pytest -q -m "not integration"` → 757 passed/47 deselected, exactly test_search_index.py; `ruff check .` and `ruff format --check .` both clean). Recording deviations from the locked Plan discovered during execution:

1. The shared campaign-create/open helper target set named in the Plan (`cli/test_lore.py`, `cli/test_region.py`) was inaccurate — neither file references campaigns at all. The actual duplication was in `cli/test_campaign.py` (left as-is; that file legitimately tests campaign create/open itself), `cli/test_index.py`, `cli/test_prime.py`, and `cli/test_encounter.py`'s own local helpers (all three switched to shared fixtures). `create_campaign`/`open_campaign`/`seed_world` ended up as CLI-only fixtures in a new `tests/cli/conftest.py`, not the root conftest, since they wrap `runner.invoke` and have no meaning outside the CLI round-trip.
2. Sharing fixtures via a root `tests/conftest.py` required removing all four `__init__.py` files under the test tree (`tests/`, `tests/cli/`, `tests/core/`, `tests/mcp/`), not anticipated by the Plan. Two collisions forced this: `packages/crypts-and-commits/tests` and `packages/demo-api/tests` are both literally named `tests` with `__init__.py`, so registering a new `tests.conftest` collided across packages; removing only the top `__init__.py` then turned `tests/mcp/` into a top-level package shadowing the real third-party `mcp` SDK dependency. The fix (removing all four) also meant helper functions had to be exposed as pytest fixture-factories (e.g. `identity(...)`, `seed_world(...)`) rather than plain importable functions, since fixture discovery is filesystem-based and immune to both collision classes.
3. Two pre-existing tests broke under the new tree-wide default identity/time mock and needed local overrides, not part of the original file list: `core/test_git_utils.py` (tests `current_git_user`'s own subprocess logic — restores the real implementation locally) and `core/test_frontmatter_utils.py::test_append_log_entry_uses_real_utc_timestamp_by_default` (explicitly checks unmocked real-time behavior — local override added). Both still pass, no assertions changed.
4. `mcp/test_encounter.py`'s `_active_campaign` fixture was NOT narrowed from `autouse=True` as planned — on inspection every one of its 21 tests genuinely depends on the campaign it creates (several assert against it directly), so the audit's "over-broad fixture" finding didn't hold up under scrutiny and narrowing it would have been a no-op change. Left as-is.

Test count unchanged at 804, no skips, no assertion/coverage changes — only fixture/setup mechanics moved or were de-duplicated, consistent with the Requirements' constraint.

### Message - 2026-08-09T04:15:31Z - John Hoff

Found and fixed a real bug during Verification, reported by the GM after running the suite in an actual terminal (not caught by the sandboxed/piped test runs used throughout implementation): `tests/cli/test_bootstrap.py::test_init_reports_behind_schema_version` and `test_init_reports_ahead_schema_version` failed with ANSI-code-laden, word-wrapped output that no longer contained the literal asserted substrings ("schema version 0"/"schema version 99").

Root cause: `cac`'s 9 CLI modules each build a module-level `console = Console()` singleton. `rich.Console.__init__` permanently bakes `COLUMNS`/`LINES`/color-system detection into `self._width`/`self._height` **at construction time** (queried from the real OS terminal or `COLUMNS`/`LINES` env vars present at that moment) - not per-print. Since these singletons are constructed at *module import time* (during pytest collection, before any fixture ever runs), a per-test `monkeypatch.setenv` fixture is structurally incapable of overriding it - confirmed empirically (a fixture-based `_stable_console` fixture, tried first, had no effect; reproduced the original failure on-demand via `COLUMNS=30 LINES=20 FORCE_COLOR=1 pdm run pytest ...`). This made `result.output` assertions silently depend on whatever real terminal window pytest happened to run inside, invisible in this environment since sandboxed tool invocations always get a wide non-tty pipe (defaults to width 80, no color).

Fix: in `tests/cli/conftest.py`, set `os.environ["COLUMNS"]`/`["LINES"]`/`["NO_COLOR"]` (and clear `FORCE_COLOR`) as plain module-level statements *before* the `from cac.cli.app import app` import in that same file - guaranteed to run first since pytest always imports a directory's `conftest.py` before any sibling test module, and no `core/`/`mcp/` module or test imports `cac.cli` (confirmed via grep), so this is the sole, earliest construction point for every `console` singleton. Verified by reproducing the original failure under `COLUMNS=30/25 LINES=20/15 FORCE_COLOR=1`, applying the fix, and reconfirming both the targeted tests and the full 804-test suite pass under that same hostile simulated terminal, and normally.

Final verification, independently re-run after this fix: `pdm run pytest -q` → 804 passed in ~26s (stable across repeated runs); `ruff check .` and `ruff format --check .` clean (one round of `ruff check --fix` removed 4 now-unnecessary `# noqa: E402` comments left over from an earlier version of this fix, since E402 isn't an enabled rule in this project's ruff config).

### Message - 2026-08-09T04:46:46Z - John Hoff

GM reported a second, different failure after the first fix: `tests/cli/test_encounter.py::test_assign_and_unassign_dependency_commands` failed with bold ANSI codes wrapping frontmatter keys (e.g. `\x1b[1marchived\x1b[0m: ...`), breaking a `"depends_on: []" in result.output` assertion. This was a distinct bug from the width issue - it's about `rich.Console`'s *color* detection, not word-wrap.

Root cause: `self._color_system` is ALSO permanently baked at `Console()` construction time, via `self._color_system = self._detect_color_system()` in `__init__`, which internally checks `self.is_terminal` (real `isatty()` on the real stdout, since construction happens during collection, before `CliRunner` ever redirects `sys.stdout`). Critically, `NO_COLOR` does **not** gate this - it only affects `export_text`/`export_html`-style export calls, not normal `console.print()`-to-stream output, so the first fix's `NO_COLOR=1` had no effect on this path. My initial verification of the first fix was a false negative: the sandboxed tool environment used to test it never has a real tty attached at process start, so `is_terminal` was already `False` there regardless of any fix, meaning the color bug was never actually exercised during that "verification."

Fix (same file, `tests/cli/conftest.py`): added `os.environ["TTY_COMPATIBLE"] = "0"` to the same pre-import module-level block. `Console.is_terminal` checks `TTY_COMPATIBLE` before `isatty()`, forcing `is_terminal` (and therefore `_color_system`) to resolve to `None`/`False` at construction regardless of the real terminal. `NO_COLOR` kept as defense-in-depth for the export-style paths.

Verified properly this time by actually reproducing a real-tty condition (not available via the sandboxed shell tool): ran pytest in-process via `pytest.main()` after replacing `sys.stdout` with a custom stream whose `isatty()` returns `True`, both confirming the bug reproduces without `TTY_COMPATIBLE=0` (`Console().color_system` == `"windows"`) and confirming it's fully suppressed with the fix (`None`), then ran both the specific failing test and the full 804-test suite in-process under that forced-real-tty condition - both clean. Also reconfirmed normally: `pdm run pytest -q` → 804 passed in ~24-27s (stable), `ruff check .` / `ruff format --check .` clean.

### Completed - 2026-08-09T04:48:09Z - John Hoff

GM confirmed clean pdm run pytest -q in their own PowerShell terminal after both console-rendering fixes (width baking + color-system baking, tests/cli/conftest.py). Final state: 804 tests passing (~24-29s, down from 72.30s baseline), ruff check/format clean, integration marker correctly scoped (pytest -q -m "not integration" deselects exactly the 47 test_search_index.py tests without affecting the default pdm run pytest -q run). All Requirements/Plan/Verification items complete; three Plan deviations and two post-hoc console-rendering bugs (discovered only once run against a real terminal, not the sandboxed/piped tool environment used throughout implementation) recorded in the Log above.
