---
assigned_lore:
- cli-mcp-parity
- console-best-practices
- skills-authored-only-in-templates
- workflow-doc-source-of-truth
name: crypts-and-commits
path: packages/crypts-and-commits
summary: 'Core `cac` Python package, console script and MCP server - the project''s
  deliverable at `packages/crypts-and-commits`. Python >=3.11 in a PDM workspace (run
  commands from the repo root). Typer CLI, MCP server, python-frontmatter, importlib.resources
  for packaged templates/docs, pytest+CliRunner, ruff (line-length 120, workspace
  root). Architecture rule: `cli/` and `mcp/` modules are thin wrappers and all domain
  logic lives in `core/`. Tests mirror `src/cac/`.'
updated_by: John Hoff
updated_on: '2026-10-28T04:02:20Z'
---

# Crypts and Commits (core library)

The core `cac` Python package, its console script and its MCP server - the deliverable of this project. Everything a developer or agent needs to know before touching code under this path.

## Tech stack / tooling

- **Python** >=3.11, managed as part of a **PDM workspace** (`[tool.pdm.workspace]` in the repo root `pyproject.toml`). Run all commands from the repository root, not this package's directory.
- **Typer** for the CLI (`cac/cli/`), one sub-`Typer` app per domain module, registered in `cli/app.py`.
- **MCP server** (`cac/mcp/`), one `@mcp.tool()` module per domain, wired into `mcp/server.py`'s `_TOOL_MODULES`; the primary agent interface, with the CLI as fallback (see `cli-mcp-parity`).
- **`python-frontmatter`** for YAML-frontmatter markdown files, via shared helpers in `core/frontmatter_utils.py` (`write_post`, `toggle_list_attribute`).
- **`importlib.resources`** to load packaged templates and docs from `core/templates/` - this is what makes them ship inside the built wheel; never load them via a raw filesystem path.
- **pytest**, using `typer.testing.CliRunner` plus `tmp_path`/`monkeypatch.chdir` fixtures for CLI tests. Tests under `tests/` mirror `src/cac/`, split into `core/`, `cli/` and `mcp/`.
- **ruff** for lint and format, `line-length = 120`, configured once at the workspace root (this package has no `[tool.ruff]` of its own).

## Architecture rule

`cac/cli/` and `cac/mcp/` modules are thin wrappers only - argument parsing, calling into `core`, and printing or returning output. All real domain logic lives in `cac/core/`, one module per concept (`world.py`, `lore.py`, `region.py`, `boss.py`, `campaign.py`, `encounter.py`, `rumors.py`, `prime.py`, `docs.py`), with supporting modules for boss candidates/provenance, campaign membership and boss coupling, short references, the search index, response budgets and recovery.

## Commands

- `pdm install` - install workspace packages and dev-dependency groups.
- `pdm run pytest -q` - full test suite.
- `pdm run ruff check .` / `pdm run ruff format .` - lint / format.
- `pdm run cac <command> --help` - exercise the CLI directly.
