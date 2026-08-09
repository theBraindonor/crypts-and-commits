---
archived: false
campaign: v0.1.8-release-readiness
created_by: John Hoff
created_on: '2026-08-09T06:20:49Z'
depends_on: []
kind: scripted
name: resolve-sourcebook-root-upward
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-08-09T14:07:06Z'
---

# Encounter

## Requirements

- Every `cac` CLI command and every `crypts-and-commits` MCP tool that reads or writes `.sourcebook/` content must resolve the project root by searching upward from the current working directory for the nearest ancestor (inclusive of cwd itself) that already contains a `.sourcebook/` directory — not by using the literal working directory unconditionally, as every such command does today via a direct `Path.cwd()` call at its own call site.
- Concretely: running any bootstrapped-project command (e.g. `cac world get`, `mcp__crypts-and-commits__lore_list`) from within a subdirectory of a bootstrapped project (e.g. `packages/crypts-and-commits`, or deeper) must operate against that project's actual `.sourcebook/` at the real root, not silently target (and, on a write, create) a nonexistent `.sourcebook/` relative to the subdirectory.
- `cac bootstrap init` is explicitly exempted from this change and keeps resolving strictly against the literal current working directory. It is the one command that establishes a project root rather than looking one up — the developer is expected to invoke it from the root they intend, and on a first run no `.sourcebook/` exists anywhere yet for an upward search to find.
- When no ancestor of the working directory (including the working directory itself) contains a `.sourcebook/` directory, behavior must be unchanged from today: whatever "not bootstrapped" error a command currently raises when run outside any project (e.g. `WorldNotFoundError`) must still be raised the same way, from the literal working directory context — this is not a behavior change for the genuinely-unbootstrapped case, only for the "bootstrapped, but invoked from a subdirectory" case.
- This is an internal resolution fix, not a new CLI flag or MCP parameter — no new user-facing option is being added for callers to override the discovered root.

## Rationale

Every `core/*.py` function already takes an explicit `root: Path` parameter and is agnostic to how that root was determined — but every call site in `cli/*.py` and `mcp/*.py` (roughly 100 call sites across `world`, `lore`, `region`, `campaign`, `encounter`, `prime`, and `index`) independently passes `Path.cwd()` directly, rather than through any shared resolution step. In this PDM workspace, an agent session's shell frequently ends up with a working directory inside a package (e.g. `packages/crypts-and-commits`) rather than the repository root where `.sourcebook/` actually lives. Reported directly by the developer: running `cac` commands from within a subpackage attempts to operate against a `.sourcebook/` relative to that subdirectory instead of the real project root, which on a write would create a stray, incorrect `.sourcebook/` directory rather than editing the real one. `core/paths.py` already owns "resolve `.sourcebook`-relative paths given a root" — this is a natural, narrow extension of that same module's responsibility to also resolve the root itself, the same way `git` walks upward from cwd to find the repository root containing `.git/`.

## Plan

1. In `core/paths.py`, add `resolve_project_root(start: Path | None = None) -> Path`: default `start` to `Path.cwd()`; check `start` and then each of `start.parents` in order (nearest first) for one where `sourcebook_dir(candidate).is_dir()` is true; return the first match. If none of `start` or its ancestors qualify, return `start` unchanged, preserving today's behavior for a genuinely unbootstrapped location (existing `_existing_*_path`-style checks in each `core` module already raise their current "not bootstrapped" errors off of `sourcebook_dir(root)` not existing).
2. Replace every direct `Path.cwd()` call across `cli/*.py` and `mcp/*.py` with `resolve_project_root()`, *except* `cli/bootstrap.py`, which keeps `Path.cwd()` as-is per the Requirements above. This touches `cli/world.py`, `cli/campaign.py`, `cli/region.py`, `cli/lore.py`, `cli/encounter.py`, `cli/prime.py`, `cli/index.py`, and `mcp/world.py`, `mcp/campaign.py`, `mcp/region.py`, `mcp/lore.py`, `mcp/encounter.py`, `mcp/prime.py`, `mcp/index.py` — every one of these already imports `Path` from `pathlib` for this exact purpose, so the change is a mechanical swap plus a `from cac.core.paths import resolve_project_root` import per file, not a structural rework of any command.
3. Add `tests/core/test_paths.py` covering `resolve_project_root`: cwd itself has `.sourcebook/` (returns cwd); cwd is a subdirectory nested under a bootstrapped root (returns the ancestor root, not cwd); no ancestor anywhere has `.sourcebook/` (returns `start` unchanged); an explicit `start` argument is honored instead of the real process cwd.
4. Add at least one CLI test (e.g. in `tests/cli/test_world.py` or a shared fixture in `tests/cli/conftest.py`) and one MCP test demonstrating a command invoked with cwd inside a subdirectory of a bootstrapped root still reads/writes the root's actual `.sourcebook/` content, not a new one under the subdirectory.
5. Checked `docs/workflow.md` (the packaged Workflow Reference Guide) for any existing claim about commands operating against "the current directory" that this change would falsify — none found; it documents the domain model and lifecycle, not root-resolution mechanics, so no update to that doc is required by this change.

## Verification

- `pdm run pytest -q` passes, including the new `tests/core/test_paths.py` cases and the new CLI/MCP subdirectory-invocation test(s).
- `pdm run ruff check .` reports zero errors and `pdm run ruff format .` reports no diffs.
- Manual check: from a bootstrapped sandbox project, `cd` into a subdirectory and run a read command (e.g. `cac world get`) and confirm it returns the root project's actual world content rather than erroring as unbootstrapped or creating a new `.sourcebook/` under the subdirectory; run a write command (e.g. `cac lore create`) from that same subdirectory and confirm the write lands under the real root's `.sourcebook/`, with no new `.sourcebook/` directory created under the subdirectory.
- Confirm `cac bootstrap init`'s behavior is unchanged (still operates strictly against the literal cwd) by running it from a subdirectory of an already-bootstrapped sandbox project and confirming it does *not* silently operate on the parent root instead.

## Log

### Review - 2026-08-09T06:23:03Z - John Hoff

Reviewed against all five applicable lore items (clean-tests-and-lint, cli-mcp-parity, console-best-practices, skills-authored-only-in-templates, workflow-doc-source-of-truth): the Plan's Verification satisfies the tests/lint gate, the Path.cwd() -> resolve_project_root() swap is applied symmetrically across cli/*.py and mcp/*.py with cli/bootstrap.py correctly and explicitly exempted so CLI/MCP parity is preserved, and the console-best-practices and skills-authored-only-in-templates lore are simply not implicated by this root-resolution-only change. The one item requiring active justification, workflow-doc-source-of-truth, is addressed in Plan step 5, which was independently confirmed by finding no reference to cwd/working-directory/root-resolution mechanics anywhere in docs/workflow.md - the no-update claim holds. No lore conflicts found; approved to proceed to reviewed.

### Completed - 2026-08-09T14:07:06Z - John Hoff

Added resolve_project_root() to core/paths.py, walking cwd and its ancestors for the nearest .sourcebook/, falling back to cwd unchanged when none found. Swapped Path.cwd() for it across all cli/*.py and mcp/*.py call sites except cli/bootstrap.py, which stays cwd-only per the Requirements. Added tests/core/test_paths.py (4 cases) plus subdirectory-invocation tests in tests/cli/test_world.py and tests/mcp/test_world.py. Verification gate passed (pdm run pytest -q: 810 passed; ruff check/format clean). Manually verified in a sandbox: a read (world get) and a write (lore create) from a subdirectory both correctly resolved to the real bootstrapped root with no stray .sourcebook/ created underneath; bootstrap init run from a subdirectory correctly stayed cwd-only, creating its own separate .sourcebook/ there rather than touching the parent.
