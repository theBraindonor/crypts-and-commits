---
assigned_lore:
- cli-mcp-parity
- console-best-practices
- skills-authored-only-in-templates
- workflow-doc-source-of-truth
name: crypts-and-commits
path: packages/crypts-and-commits
summary: 'Core `cac` Python package and console script - the project''s deliverable
  at `packages/crypts-and-commits`. Python >=3.11 in a PDM workspace (run commands
  from the repo root). Typer CLI, python-frontmatter, importlib.resources for packaged
  templates, pytest+CliRunner, ruff (line-length 120, configured at the workspace
  root). Architecture rule: `cli/` modules are thin wrappers and all domain logic
  lives in `core/` (one module per concept). Tests mirror `src/cac/`.'
updated_by: John Hoff
updated_on: '2026-07-28T03:53:02Z'
---

# Crypts and Commits (core library)

The core `cac` Python package and its console script - the deliverable of this project. Everything a developer or agent needs to know before touching code under this path.

## Tech stack / tooling

- **Python** >=3.11, managed as part of a **PDM workspace** (`[tool.pdm.workspace]` in the repo root `pyproject.toml`). Run all commands from the repository root, not this package's directory.
- **Typer** for the CLI (`cac/cli/`), one sub-`Typer` app per domain module, registered in `cli/app.py`.
- **`python-frontmatter`** for YAML-frontmatter markdown files, via shared helpers in `core/frontmatter_utils.py` (`write_post`, `toggle_list_attribute`).
- **`importlib.resources`** to load packaged templates from `core/templates/` - this is what makes templates ship inside the built wheel; never load them via a raw filesystem path.
- **pytest**, using `typer.testing.CliRunner` plus `tmp_path`/`monkeypatch.chdir` fixtures for CLI tests. Tests under `tests/` mirror `src/cac/` exactly, split into `core/` and `cli/`.
- **ruff** for lint and format, `line-length = 120`, configured once at the workspace root (this package has no `[tool.ruff]` of its own).

## Architecture rule

`cac/cli/` modules are thin wrappers only - argument parsing, calling into `core`, and printing output. All real domain logic lives in `cac/core/`, one module per concept (`world.py`, `lore.py`, `region.py`, `campaign.py`, `encounter.py`).

## Commands

- `pdm install` - install workspace packages and dev-dependency groups.
- `pdm run pytest -q` - full test suite.
- `pdm run ruff check .` / `pdm run ruff format .` - lint / format.
- `pdm run cac <command> --help` - exercise the CLI directly.
