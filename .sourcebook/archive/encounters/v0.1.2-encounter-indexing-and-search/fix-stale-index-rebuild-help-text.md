---
archived: true
campaign: v0.1.2-encounter-indexing-and-search
created_by: John Hoff
created_on: '2026-07-28T00:22:38Z'
depends_on: []
name: fix-stale-index-rebuild-help-text
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-08-02T22:13:48Z'
---

## Requirements

Correct the `cac index` CLI help text, which still describes pre-`sync-index-on-write` behavior:

- `packages/crypts-and-commits/src/cac/cli/index.py`'s `Typer` app-level `help` string currently reads: "Build and inspect the search index over .sourcebook content. The index is derived data, regenerated from disk by 'rebuild' - it is not kept in sync automatically." This is now factually wrong - since `sync-index-on-write` (this same campaign), every `cac`-driven create/update/delete incrementally patches the index, and `rebuild` is only needed for the first-ever build and for catching up on changes made outside `cac` (`git pull`, branch checkout, merge, manual edits).
- The corrected text must accurately describe both facts: (a) the index self-updates on ordinary `cac` writes, no separate command required, and (b) `rebuild` remains necessary for the initial build and for resyncing after non-`cac` changes to `.sourcebook`.
- Scope check: grep across the repo (excluding `.venv/`) turns up exactly this one stale string - no other CLI help, MCP tool docstring, or `.md` doc repeats the "not kept in sync automatically" claim, so this is a single-string fix, not a multi-file sweep.
- No behavior change - this is a documentation/help-text-only correction. No code paths, tests, or MCP tools are affected.

## Rationale

An agent or developer falling back to the CLI (per this project's MCP-first, CLI-fallback design) reads `cac index -h` to understand the index's operating model. Leaving the old claim in place would actively mislead them into running `cac index rebuild` after every change, defeating the point of the `sync-index-on-write` work and reintroducing the exact operational burden it removed. This was missed by that encounter's Verification because it was correctly scoped to the `core` layer (per `cli-mcp-parity`'s transparency requirement - no CLI/MCP code needed to change), but the pre-existing help *text* describing the old model was never part of that Plan and needs its own pass.

## Plan

1. In `packages/crypts-and-commits/src/cac/cli/index.py`, replace the `Typer(help=...)` string with accurate copy, e.g.: "Build and inspect the search index over .sourcebook content. The index stays in sync automatically as content is created, updated, or deleted through cac - 'rebuild' is only needed for the first build, or to catch up on changes made outside cac (e.g. a git pull)."
2. Spot-check the `status`/`rebuild`/`search` command docstrings in the same file for any similar stale phrasing; update only if found (expected: none, based on the current read of the file).
3. No changes needed elsewhere - confirmed by the repo-wide grep for "kept in sync"/"regenerated from disk" in the Requirements section above.

## Verification

- `pdm run pytest -q` (full suite) passes - no test currently asserts on this help string's exact wording, so this should be a no-op for tests, but confirm.
- `pdm run ruff check .` passes with zero errors; `pdm run ruff format .` leaves no diff.
- Manual check: `pdm run cac index --help` (or the built `cac index -h`) prints the corrected description.

## Log

### Review - 2026-07-28T00:25:00Z - John Hoff

Reviewed against clean-tests-and-lint, cli-mcp-parity, and console-best-practices: the Plan is a narrowly-scoped, no-behavior-change help-text correction that honors clean-tests-and-lint via its Verification steps (pytest + ruff), correctly falls outside cli-mcp-parity's command-parity trigger since no command is added or changed (confirmed by reading the named file, whose help string matches the Requirements verbatim), and doesn't implicate console-best-practices since a Typer app help string is CLI-authored text, not stored .sourcebook body content requiring markup=False. One unverified-but-plausible claim: the Requirements assert a repo-wide grep found no other stale "not kept in sync" phrasing in any CLI help or MCP docstring, which the reviewer couldn't check within the bounded review surface (only cli/index.py was named) - worth a quick re-confirmation during execution, per the Plan's own step 3, but not a blocker. PASS-WITH-NOTES.

### Completed - 2026-07-28T00:27:54Z - John Hoff

Corrected the cac index Typer app help string in cli/index.py to describe the current sync-on-write behavior (index self-updates on cac writes; rebuild is only for the first build or catching up on non-cac changes). Spot-checked status/rebuild/search docstrings in the same file - no similar stale phrasing found. Re-ran the repo-wide grep for "kept in sync"/"regenerated from disk" - no remaining matches outside this encounter's own tracking file. Verification: pdm run pytest -q (672 passed), ruff check . clean, ruff format . no diff, and manually confirmed via cac index --help that the corrected text prints.
