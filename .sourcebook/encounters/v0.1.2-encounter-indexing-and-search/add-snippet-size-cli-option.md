---
campaign: v0.1.2-encounter-indexing-and-search
created_by: John Hoff
created_on: '2026-07-27T04:29:16Z'
depends_on: []
name: add-snippet-size-cli-option
regions:
- crypts-and-commits
status: draft
updated_by: John Hoff
updated_on: '2026-07-27T04:29:21Z'
---

## Requirements

- Expose the FTS5 `snippet()` token count - currently the hardcoded `_SNIPPET_TOKENS = 12` module constant in `core/search_index.py` - as a `cac index search` CLI option, rather than a fixed value.
- Default value changes from `12` to **`20`** tokens.
- `core/search_index.py`'s `search()` function should accept the token count as a parameter (rather than reading the module constant directly), so `cli/index.py` can pass the CLI option's value through.
- SQLite's `snippet()` caps this value at 64 tokens - decide during implementation whether to clamp, reject, or pass through an out-of-range value.

## Rationale

To be refined when this encounter is picked up for work.

## Plan

To be refined when this encounter is picked up for work.

## Verification

- `pdm run pytest -q` passes, with no skips or deletions used to dodge a failure.
- `pdm run ruff check .` reports zero errors and `pdm run ruff format .` reports no diffs.
