---
campaign: v0.1.0-bootstrapping
name: fix-rich-markup-body-rendering
regions:
- crypts-and-commits
status: completed
---

# Fix Rich Markup Body Rendering

## Requirements

- `cac world get`, `cac lore get`, `cac region get`, `cac campaign get`, and `cac encounter get` must print a body's markdown content verbatim - no character sequences silently dropped or altered.
- The fix must not change frontmatter rendering (still printed as `key: value` lines above the body) or any other command's behavior.
- No change to how bodies are stored on disk - this is a display-only bug.

## Rationale

`cli/world.py`, `cli/lore.py`, `cli/region.py`, `cli/campaign.py`, and `cli/encounter.py` each construct a `rich.Console()` with default settings and call `console.print(body)` in their `get` command. Rich's default `Console` has `markup=True`, so any `[...]` in the body is parsed as Rich markup: unrecognized tags are silently stripped. This was discovered first-hand while writing the `crypts-and-commits` and `demo-ui` region bodies - `[tool.pdm.workspace]`, `[tool.ruff]`, and a `[[demo-api]]` wiki-link all vanished from `cac region get` output even though the underlying markdown file was correct. Any lore/region/campaign/encounter body that happens to contain brackets (TOML table headers, markdown link references, code showing list/array syntax, etc.) is silently corrupted on display.

## Plan

1. In each of `cli/world.py`, `cli/lore.py`, `cli/region.py`, `cli/campaign.py`, `cli/encounter.py`, find the `console.print(body)` call in the `get` command and pass `markup=False` so body content is always printed literally.
2. Leave frontmatter-line printing (`console.print(f"[bold]{key}[/bold]: {value}")` or similar) using markup as-is, since those lines are constructed by the CLI itself, not user content - only body printing is affected.
3. Add or update a CLI test per module asserting that a body containing bracketed text (e.g. `[tool.pdm.workspace]`) round-trips unchanged through `get` output.
4. Run the full test suite and ruff per the clean-tests-and-lint lore item before considering this done.

## Verification

- `pdm run pytest -q` passes, including new bracket round-trip tests for each of the five `get` commands.
- `pdm run ruff check .` reports zero errors and `pdm run ruff format .` leaves no diffs.
- Manual smoke test: `cac region get crypts-and-commits` (and `demo-ui`) shows `[tool.pdm.workspace]` / `[tool.ruff]` intact in the output, matching the raw file content.
