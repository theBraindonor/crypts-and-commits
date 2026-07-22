# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project state

This repository is currently a bare scaffold — there is no source code, package layout, or test suite yet. Only `pyproject.toml`, `LICENSE` (Apache-2.0), and `.gitignore` exist. When adding the first code, establish the package structure under a `src/` or top-level package directory consistent with `pyproject.toml`'s project name, and update this file with the real commands and architecture once they exist.

## Project purpose

Crypts and Commits ("C&C") is a Coding Assistant Continuity Framework. It uses a tabletop-gaming metaphor to describe collaboration between a developer and an AI coding assistant: the developer acts as the Game Master, establishing context, making decisions, and retaining final authority over the session.

## Tooling

- Package/dependency manager: **PDM** (`pyproject.toml` has `[tool.pdm]` with `distribution = false`, meaning this is a non-distributable/application-style project, not a publishable library).
- Python: requires `>=3.11`.
- Common commands:
  - `pdm install` — install dependencies into `.venv`
  - `pdm add <package>` — add a dependency
  - `pdm run <script>` — run a script/command inside the project environment

No lint, test, or build tooling is configured yet — do not assume `pytest`, `ruff`, or `mypy` conventions are in place until they appear in `pyproject.toml` (the `.gitignore` already anticipates `.mypy_cache/`, `.pytest_cache/`, and `.ruff_cache/`, suggesting `mypy`, `pytest`, and `ruff` are the intended future toolchain).
