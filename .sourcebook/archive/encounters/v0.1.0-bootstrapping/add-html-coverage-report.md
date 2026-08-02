---
archived: true
campaign: v0.1.0-bootstrapping
created_by: John Hoff
created_on: '2026-07-25T06:16:44Z'
depends_on: []
name: add-html-coverage-report
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-08-02T22:00:20Z'
---

# Add HTML Coverage Report

## Requirements

- Unit tests can produce an HTML coverage report for the `cac` package (`packages/crypts-and-commits/src/cac`) via a single documented `pdm run` command.
- The dependency needed to generate coverage is declared in the workspace's PDM dev-dependency groups and locked, so `pdm install` provisions it for every contributor without manual steps.
- Coverage generation does not run by default under the existing `pdm run pytest -q` invocation (the command gated by the `clean-tests-and-lint` lore before any encounter's Verification is considered complete) — it stays a separate, opt-in command so the default test run's speed and output are unaffected.
- Generated coverage artifacts (`htmlcov/` and `.coverage`) are excluded from Git.
- The new command is documented in `CLAUDE.md`'s Tooling section alongside the existing `pdm run pytest -q` / `pdm run ruff` bullets.

## Rationale

As `cac`'s `core`/`cli` modules keep growing across encounters, an HTML coverage report gives a fast, visual way to spot untested branches, complementing pass/fail results with an at-a-glance completeness signal. No coverage tooling exists in the workspace today. `pytest-cov` is the standard pytest-integrated coverage plugin and produces both terminal and HTML output without additional tooling, so it is the natural fit for a project already standardized on pytest. Keeping report generation opt-in (rather than folded into `pdm run pytest -q`'s default invocation) avoids adding runtime overhead and unrelated console output to the command every encounter's Verification step already relies on via `clean-tests-and-lint`.

## Plan

1. Add `pytest-cov` to the `test` dev-dependency group in the root `pyproject.toml`.
2. Run `pdm lock -d -G:all` to refresh the lock file, then `pdm install` to provision `.venv` with the new dependency.
3. Add a `[tool.coverage.run]` table to the root `pyproject.toml` scoping coverage collection to the `cac` package (`source = ["cac"]`), and a `[tool.coverage.html]` table if a non-default output directory (`htmlcov/`, the pytest-cov default) needs to be pinned explicitly. Keep the invocation short: `pdm run pytest --cov --cov-report=html -q`.
4. Add `htmlcov/` and `.coverage` entries to the root `.gitignore`.
5. Document the new command in `CLAUDE.md`'s Tooling section, e.g. `pdm run pytest --cov --cov-report=html -q` — generates `htmlcov/index.html`.

## Verification

- Run `pdm run pytest --cov --cov-report=html -q` from the repository root; confirm it exits successfully and `htmlcov/index.html` is generated.
- Run `pdm run pytest -q` (no coverage flags) and confirm it still passes unaffected, with no coverage-related output.
- Run `pdm run ruff check .` and `pdm run ruff format .` to confirm the `clean-tests-and-lint` lint gate is unaffected by the `pyproject.toml`/`.gitignore` changes.
- Run `git status` and confirm `htmlcov/` and `.coverage` do not appear as untracked files.

## Log

### Review - 2026-07-25T06:18:13Z - John Hoff

Reviewed against both applicable lore items. clean-tests-and-lint is honored: the Plan keeps 'pdm run pytest --cov --cov-report=html -q' as a separate opt-in command, explicitly re-verifies 'pdm run pytest -q' and ruff stay clean/unaffected. console-best-practices isn't implicated - the Plan adds no console.print calls or cac/cli/* changes, so it's vacuously satisfied; note the encounter's region (crypts-and-commits, path packages/crypts-and-commits) doesn't closely match the Plan's actual footprint, which is almost entirely workspace-root files (pyproject.toml, .gitignore, CLAUDE.md) - not a lore conflict, just a scope observation. Verified the Plan's factual assumptions (existing test dev-dependency group, absence of prior coverage config/gitignore entries) directly against pyproject.toml and .gitignore; both check out. No conflicts found.

### Message - 2026-07-25T06:23:22Z - John Hoff

Deviation: 'pdm lock -d -G:all' (needed to add pytest-cov to the test group) re-resolved every dev-dependency group, bumping ruff 0.15.22 -> 0.16.0 as a side effect. The newer ruff surfaced 44 pre-existing lint findings unrelated to this encounter's own changes (confirmed via git stash: identical findings without my edits). Fixed under clean-tests-and-lint rather than deferred: ruff --fix auto-fixed 43 (import sorting, RUF020 redundant NoReturn, UP035 typing -> collections.abc migration); the remaining PLW1510 finding in core/git_utils.py was fixed manually by adding explicit check=False to the existing subprocess.run call, matching its existing intent of inspecting returncode itself rather than raising. All 486 tests still pass and ruff is clean after the fixes.

### Message - 2026-07-25T06:26:38Z - John Hoff

Added an out-of-plan hardening fix at the user's request: core/git_utils.py's subprocess.run call for 'git config user.name' now passes stdin=subprocess.DEVNULL explicitly. Motivation: this codebase's long-term goal is an MCP server (see CLAUDE.md's mcp/ section) that will run as a long-lived process communicating over stdio - its own stdin carries the live JSON-RPC request stream. Without an explicit stdin redirect, a subprocess spawned from within that server would inherit that same stdin handle by default (subprocess.run's capture_output=True only redirects stdout/stderr, not stdin), risking a hang or protocol corruption if the child ever reads from it. stdin=DEVNULL removes that risk unconditionally, independent of whether MCP exists yet. No other subprocess.run call sites exist in packages/crypts-and-commits/src today (confirmed via grep). Re-ran full verification after the change: pdm run pytest --cov --cov-report=html -q (486 passed, htmlcov/index.html regenerated), pdm run ruff check . and ruff format . (both clean).

### Completed - 2026-07-25T06:28:03Z - John Hoff

HTML coverage reporting added via pytest-cov, wired as an opt-in 'pdm run pytest --cov --cov-report=html -q' command separate from the default test-suite invocation. Verified: coverage run passes and produces htmlcov/index.html; default 'pdm run pytest -q' and ruff remain clean; coverage artifacts are gitignored. Also hardened core/git_utils.py's subprocess call with stdin=DEVNULL ahead of future MCP stdio-transport use, at the user's request mid-encounter.
