---
archived: false
campaign: v0.1.8-release-readiness
created_by: John Hoff
created_on: '2026-08-09T02:26:40Z'
depends_on: []
kind: scripted
name: add-nox-multi-python-testing
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-08-09T02:55:05Z'
---

# Add nox for pre-release multi-Python-version test runs

## Requirements

- Add `nox` (and any supporting plugin identified as necessary in the Plan, e.g. for PDM-workspace integration) as a dev-dependency of the root workspace `pyproject.toml`, in a **new, non-default dev-dependency group** — not merged into the existing `dev`/`test`/`lint` groups — so a bare `pdm install` never pulls it in.
- Configure a `noxfile.py` with a parametrized test session covering Python **3.11, 3.12, 3.13, and 3.14**, running the existing test suite (`pytest -q` against `testpaths = ["packages"]`, matching the root `[tool.pytest.ini_options]`) under each interpreter.
- The nox session must correctly exercise the PDM workspace's local packages (at minimum `crypts-and-commits`, the package actually heading toward publication) in each environment - decide in the Plan whether `demo-api` (not published, `distribution = false`) is included or out of scope if its own dependency floors don't cleanly support all four versions.
- Running nox must **not** become part of the routine dev loop: `pdm run pytest -q`, `pdm install`, and the other commands already documented in `CLAUDE.md`'s Tooling section must keep their current behavior unchanged and must not implicitly invoke nox. Nox is a manual, explicitly-invoked pre-release gate (e.g. `pdm run nox`), not a per-commit or per-test-run check.
- Document how a developer provisions the four required interpreters locally, and how the nox session is expected to discover/obtain them - this matters concretely here since this dev machine currently only has Python 3.12 and 3.13 as standard installs plus 3.11 via `uv`, and has no 3.14 at all. Investigate whether nox's `uv`-backed virtualenv support (`venv_backend="uv"`) can auto-provision missing interpreters, which could remove the need for separate manual provisioning.
- `CLAUDE.md`'s Tooling section gains a short entry for the new command, consistent with how every other workspace command is already documented there.

## Rationale

The `v0.1.8-release-readiness` campaign's punch-list explicitly names "a CI/publish workflow" as a candidate area to survey before `cac`'s first public release. `packages/crypts-and-commits/pyproject.toml` declares `requires-python = ">=3.11"`, but the test suite is only ever actually exercised under whichever single interpreter happens to back a developer's `.venv` - there's no verification that `cac` actually works across the range of Python versions it claims to support. Adding nox closes that gap as a pre-release gate, without slowing down the routine edit/test loop, which is why it's scoped as an explicitly-invoked, non-default tool rather than something wired into `pdm run pytest -q` or CI. Nox (a Python-native, session-based runner) was chosen over tox for this project after consideration - it avoids tox's separate ini/toml configuration language in favor of plain Python sessions, and its `uv` virtualenv backend offers a plausible built-in answer to the interpreter-provisioning problem this encounter otherwise has to solve by hand.

## Plan

1. Investigate how nox best coexists with this PDM workspace (single root `pyproject.toml` with `[tool.pdm.workspace]`, local editable packages installed via `-e file:///...`) - evaluate whether a session should shell out to `pdm install`/`pdm sync` to build the workspace packages, versus nox's own `session.install(...)`. Check whether `cac`'s current dependencies (including the recently-upgraded `mcp>=2.0.0`) and `demo-api`'s dependencies already publish wheels compatible with Python 3.14, since it's new enough that some transitive dependencies may lag.
2. Decide the interpreter-provisioning story for all four versions, given this machine's current gap (3.12/3.13 standard installs, 3.11 via `uv`, no 3.14) - specifically evaluate nox's `venv_backend="uv"` for auto-provisioning missing interpreters versus requiring `uv python install`/manual installs up front. Record the decision and get the user's sign-off before implementing, since it determines the rest of this plan's shape.
3. Add `nox` (and any plugin chosen above) to a new dev-dependency group in the root `pyproject.toml`; run `pdm lock -d -G:all` (required for any new dev-dependency group per `CLAUDE.md`) followed by `pdm install` for that group only as needed.
4. Write `noxfile.py` with a session parametrized across `["3.11", "3.12", "3.13", "3.14"]`, each running `pytest -q` against `testpaths = ["packages"]`.
5. Run the new command across all four versions locally and fix anything version-specific that surfaces.
6. Update `CLAUDE.md`'s Tooling section with the new command; confirm `pdm run pytest -q`, `pdm run ruff check .` / `ruff format .`, and `pdm install` all keep their existing behavior unchanged.

## Verification

- The new nox invocation completes successfully across all four declared Python versions (3.11, 3.12, 3.13, 3.14), running the full `packages/` test suite in each.
- `pdm run pytest -q` and `pdm run ruff check .` / `pdm run ruff format .` remain clean, with unchanged invocation and behavior - nox is not wired into either.
- A bare `pdm install` does not install `nox` or its plugins (confirmed via `pdm list` or equivalent showing the new group excluded by default).
- `CLAUDE.md` documents the new command.

## Log

### Review - 2026-08-09T02:32:39Z - John Hoff

Reviewed against all five applicable lore items: clean-tests-and-lint is explicitly honored via the Verification section (pytest and ruff must stay clean, unchanged invocation); cli-mcp-parity, console-best-practices, skills-authored-only-in-templates, and workflow-doc-source-of-truth are not triggered since the Plan touches none of cli/, mcp/, console output, skill templates, or the domain model/workflow procedure — nox is being correctly documented in CLAUDE.md's Tooling section instead, matching existing convention. No lore conflicts found. One unverified concern noted: the encounter is assigned to the crypts-and-commits region (path packages/crypts-and-commits) but its actual targets (root pyproject.toml, root noxfile.py, root CLAUDE.md) sit outside that documented path — likely fine if no narrower workspace-root region exists, but worth a quick confirmation. The Plan appropriately gates the interpreter-provisioning and Python-3.14-compatibility decisions on investigation and user sign-off before implementation.

### Message - 2026-08-09T02:49:19Z - John Hoff

Scope clarification per user feedback: the "bare pdm install does not install nox" Verification bullet is relaxed. PDM installs all [tool.pdm.dev-dependencies] groups by default (confirmed - this is documented, pre-existing behavior for the dev/test/lint groups too, not something this encounter changes), so nox does end up in the root workspace .venv on a plain pdm install. The user's actual concerns were (1) nox never gets invoked as part of the routine pdm run pytest -q loop, and (2) nox never becomes a dependency of packages/crypts-and-commits/pyproject.toml (the package actually being distributed) - both remain true and are unaffected by this relaxation, since nox was only ever added to the root workspace pyproject.toml's dev-dependencies, never to crypts-and-commits' own pyproject.toml.

### Completed - 2026-08-09T02:55:05Z - John Hoff

nox added as a pre-release multi-Python-version test gate. noxfile.py runs crypts-and-commits' test suite under 3.11/3.12/3.13/3.14 via the uv venv backend (auto-downloads missing interpreters - verified against 3.14, which wasn't installed locally). Scoped to crypts-and-commits only (demo-api excluded - its workspace-relative dependency on crypts-and-commits doesn't resolve outside the PDM workspace, and it isn't published). nox lives only in the root workspace pyproject.toml's dev-dependencies, never in crypts-and-commits' own pyproject.toml, and is never invoked by pdm run pytest -q or any other routine command. Per user clarification, the "bare pdm install excludes nox" verification bullet was relaxed - PDM installs all dev-dependency groups by default, which is fine since the two real concerns (no routine invocation, no leak into crypts-and-commits' own dependency list) both hold. pytest (804 passed) and ruff check/format clean throughout.
