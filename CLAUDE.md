# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project purpose

Crypts and Commits ("CAC") is a Coding Assistant Continuity Framework. It uses a tabletop-gaming metaphor to describe collaboration between a developer and an AI coding assistant: the developer acts as the Game Master, establishing context, making decisions, and retaining final authority over the session. Use "CAC", not "C&C", as the project's abbreviation — it aligns with the "Coding Assistant Continuity" subtitle and avoids reading as a direct D&D reference.

The framework's own CLI (`cac`) is meant to be driven by the coding assistant, not just the developer — it is the mechanism by which an agent records project context and tracks its own work. This repository dogfoods that idea: its own `.sourcebook` (see below) is live — a populated world summary, lore, regions, and campaign/encounter history — and is the actual source of truth for project context and in-flight work, not a placeholder. Before starting any nontrivial work in this repository, use the `world-manager` skill to prime context (world summary, applicable lore, relevant region) and the `campaign-manager` skill to check for an open encounter covering the task; if none exists, ask the user whether to create one before proceeding. The longer-term goal is using the same framework to drive AI-assisted work on *other* projects.

## Guardrail: `.sourcebook/` is MCP/CLI-only

Once a project has been bootstrapped, its `.sourcebook/` directory is managed exclusively through the `crypts-and-commits` MCP server's tools (`world_get`, `lore_*`, `region_*`, `campaign_*`, `encounter_*` — one module per domain in `mcp/`), falling back to the equivalent `cac` CLI commands (`cac world`, `cac lore`, `cac region`, `cac campaign`, `cac encounter`) only when the MCP server isn't available for a session — never by creating, reading, editing, moving, or deleting files under `.sourcebook/` directly, whether with the `Edit`/`Write`/`Read` tools or via `Bash` (`rm`, `mv`, `sed -i`, `cat`, shell redirection, etc.). The long-term goal is for the coding assistant to have **no awareness of the `.sourcebook` directory's existence at all**; the MCP server now covers every command except `bootstrap` (see the `cli-mcp-parity` region lore, which keeps that property enforced going forward), and is the primary interaction layer today, not a future placeholder.

`Edit(.sourcebook/**)` is denied in `.claude/settings.json` — and, per Claude Code's permission-rule semantics, `Edit(path)` rules cover all file-editing tools including `Write`, so this single rule already blocks both; a separate `Write(.sourcebook/**)` entry would be accepted but silently unenforced (only `Edit`/`Read` path rules are matched), so don't add one. `Read` is deliberately **not** blocked either: skill instructions should still prefer the MCP `get`/`list` tools (or their `cac ... get`/`list`/etc. CLI-fallback forms) over reading files directly, but nothing yet technically prevents a direct `Read`. Treat the MCP/CLI-only rule itself as binding even where it isn't (yet) fully technically enforced.

For Codex, `cac bootstrap init` also deploys a project-local `.codex` `PreToolUse` hook that blocks direct shell and `apply_patch` references to `.sourcebook/`. The hook is a guardrail, not a complete sandbox boundary: Codex hooks can miss specialized tool paths and shell filtering cannot exhaustively recognize every possible filesystem write. The `crypts-and-commits` MCP tools and `cac` CLI remain the approved sourcebook interfaces. Newly deployed project hooks require the developer to review and trust them through Codex's `/hooks` workflow before they run.

`cac bootstrap init` is invoked by the **developer only** — the coding assistant must never run it itself, even to fix a missing `.sourcebook`. If `.sourcebook` is missing, ask the user to bootstrap the project.

This restriction is about `.sourcebook/` *content*, not the `cac` source code itself — freely edit `packages/crypts-and-commits/src/cac/**` and its tests as normal.

`cac bootstrap init` provisions (creates, or merges into an existing) `.claude/settings.json` with this same `.sourcebook/**` Edit deny rule, an `allow` entry for the MCP server, and a matching `enabledMcpjsonServers` entry, for whatever project it bootstraps — the guardrail no longer has to be set up by hand as it was in this repo before this was implemented.

## Repository layout

This is a [PDM workspace](https://pdm-project.org/en/latest/usage/monorepo/) (`[tool.pdm.workspace]` in the root `pyproject.toml`) containing independent packages:

- `packages/crypts-and-commits` — the core framework: the `cac` Python package and its `cac` console script.
- `packages/demo-api` — a demonstration API used for development testing within the project (not a distributable library — `distribution = false`).
- `packages/demo-ui` — a demonstration Node.js UI exercising the demo API. *(Not yet added.)*

## Tooling

- Package/dependency manager: **PDM**. Run commands from the repository root.
  - `pdm install` — install all workspace packages and dev-dependency groups into `.venv`
  - `pdm run pytest -q` — run the full test suite (configured via root `[tool.pytest.ini_options]`, `testpaths = ["packages"]`)
  - `pdm run pytest packages/crypts-and-commits/tests/core/test_lore.py -q` — run a single test file/module
  - `pdm run pytest --cov --cov-report=html -q` — run the full test suite plus an HTML coverage report for the `cac` package (`[tool.coverage.run]` in root `pyproject.toml`), written to `htmlcov/index.html` (gitignored); opt-in only, not part of the default `pdm run pytest -q` invocation
  - `pdm run nox` — pre-release check: run the `crypts-and-commits` package's test suite under Python 3.11, 3.12, 3.13, and 3.14 (`noxfile.py`, uses the `uv` venv backend to auto-download any interpreter missing locally); manual/explicit only, never invoked by `pdm run pytest -q` or any other routine command
  - `pdm run ruff check .` / `pdm run ruff format .` — lint / format (root `[tool.ruff]`, `line-length = 120`; a single root config applies workspace-wide, since nested `pyproject.toml` files have no `[tool.ruff]` table of their own)
  - `pdm run cac <command> --help` — exercise the CLI directly against the current working directory
- Python: requires `>=3.11`.
- Adding a *new* PDM dev-dependency group requires `pdm lock -d -G:all` before `pdm install` will recognize it.
- In this workspace, `cac` is only on `PATH` via `pdm run cac ...` (the package is an editable install inside the workspace `.venv`, not a global install). This is a wrinkle of this repo's own dev setup — skill content (see below) invokes `cac` generically and should not encode `pdm run`.

## Architecture: the `cac` package

`packages/crypts-and-commits/src/cac/` is split into three subpackages, with a strict rule: **CLI modules are thin wrappers only — all real logic lives in `core`.**

- `core/` — domain logic, one module per concept (`world.py`, `lore.py`, `region.py`, `campaign.py`, `encounter.py`), plus shared infrastructure:
  - `config.py` — all directory/file names, regex patterns, and status enums in one place.
  - `paths.py` — resolves the `.sourcebook` directory relative to a project root.
  - `frontmatter_utils.py` — shared helpers (`write_post`, `toggle_list_attribute`) for reading/writing YAML-frontmatter markdown via `python-frontmatter`.
  - `templates/` — packaged, non-Python template files loaded via `importlib.resources` (critical: this is what makes templates ship inside the built wheel). Templates are grouped into subpackages by purpose: `templates/sourcebook/` holds the `.md` templates for the domain objects below; `templates/skills/{claude,codex}/{world_manager,campaign_manager}/` holds the packaged agent-skill flavors deployed by `cac bootstrap init` (see "Agent skills" below); `templates/codex/` holds the Codex `PreToolUse` sourcebook-guard hook script deployed alongside the guardrail described above; `templates/docs/` holds `workflow.md`, the Workflow Reference Guide — the framework's source of truth for the `.sourcebook` domain model's structure and workflow procedure (see the `workflow-doc-source-of-truth` region lore).
  - `bootstrap.py` — creates the `.sourcebook` directory and seeds `world.md`.
- `cli/` — one Typer module per `core` module, registered as a sub-`Typer` app in `cli/app.py` (two-tier help: `cac -h` lists modules, `cac <module> -h` lists that module's commands). `cli/common.py` holds shared helpers (`edit_markdown` — opens `$EDITOR` with a `.txt` extension even though the underlying file is `.md`; `fail` — prints and exits non-zero). Every `get` command prints its body via `console.print(body, markup=False)` — `rich.Console` defaults to `markup=True`, which silently strips bracketed text (e.g. `[tool.pdm.workspace]`) from anything rendered without that flag; any new command that prints stored content should do the same.
- `mcp/` — the MCP server exposing `.sourcebook` operations to agents: one module per domain (`world.py`, `lore.py`, `region.py`, `campaign.py`, `encounter.py`, plus `prime.py`), each a thin `@mcp.tool()`-decorated wrapper calling straight into `core/`, wired together in `server.py` via `_TOOL_MODULES`. This is now the primary interaction layer for `.sourcebook` — the CLI (above) is retained as a fallback for when the MCP server isn't available for a session. `bootstrap` is the one command family intentionally never exposed here (developer-only, see the guardrail above).

Tests under `packages/crypts-and-commits/tests/` mirror the `src/cac/` package structure exactly (one test module per source module, split into `core/` and `cli/`).

## The sourcebook domain model

Bootstrapping a project (`cac bootstrap init`) creates a `.sourcebook/` directory in the project root holding these object types, all stored as markdown files with YAML frontmatter:

- **`world.md`** (singleton) — summary of the project's goals/purpose. Used to build context before applying world-level lore. Tracks `assigned_lore`.
- **`lore/<name>.md`** — a standard, convention, or best practice used to review encounters before work begins. Lore assigned to the world is global (applies to every encounter); otherwise it only applies when assigned to a region the encounter takes place in. Tracks `enabled`, `assigned_to_world`, `assigned_regions`.
- **`region/<name>.md`** — a path within the repository needing its own documentation and lore (e.g. "frontend" vs. "backend" in a web app). Has a `path` attribute (not validated against the filesystem — regions may be aspirational) and tracks `assigned_lore`.
- **`campaigns/<name>.md`** — a long-running initiative, analogous to a Jira "Epic" (e.g. "Create the MVP"), expected to span many encounters before completion. Has a `status`: `draft`, `open`, `completed`, `abandoned`.
- **`encounters/<campaign>/<name>.md`** — a concrete unit of work within a campaign: a plan the agent is expected to execute, with fixed body sections (`Requirements`, `Rationale`, `Plan`, `Verification`). Has a code-enforced `status` lifecycle: `draft` (only status where those four sections may be replaced) → `reviewed` (once world/region lore checks pass, via `cac encounter review`, which locks the sections) → `open` (once the user approves and every direct dependency is completed, via `cac encounter open`) → `completed` (once work and verification finish and the user confirms, via `cac encounter complete`); `abandoned` is reachable from `draft`, `reviewed`, or `open` (via `cac encounter abandon`) but not from `completed`. Also has a `regions` list (an encounter may apply to one or more regions' lore; assignment is recorded only on the encounter, not back on the region) and a `depends_on` list of direct prerequisite encounter names within the same campaign.

Cross-object linking always lives on the "target" object's `core` module (e.g. `world.py` owns `assign_lore`/`unassign_lore`, `region.py` owns its own `assign_lore`/`unassign_lore`), while the corresponding CLI commands live under the "source" object being assigned (e.g. `cac lore assign-world`, `cac lore assign-region`, `cac encounter assign-region`).

Known limitation: deleting a lore/region/campaign entry does not cascade-clean stale references left in objects that were assigned to it.

## Agent skills

Two functionally-equivalent sets of skills wrap the `crypts-and-commits` MCP server (falling back to the CLI when it's unavailable) so an agent session can drive `.sourcebook` content without ever touching it directly, per the guardrail above: Claude Code originals under `.claude/skills/`, and a Codex-native mirror under `.agents/skills/` (referencing the same MCP tools by their bare registered names, since Codex's MCP invocation surface doesn't share Claude Code's `mcp__crypts-and-commits__`-prefixed form; see `AGENTS.md`).

- **`world-manager`** — the static world-building context: world/lore/region tools. Never calls `bootstrap` (developer-only, see the guardrail section, and intentionally not exposed over MCP at all).
- **`campaign-manager`** — the active work-tracking loop: campaign/encounter tools, including the lore-review gate before an encounter moves `draft` → `reviewed` → `open` and the verification/confirmation step before `open` → `completed`.

`cac bootstrap init` packages both flavors and deploys them into a target project's `.claude/skills/`/`.agents/skills/` (via `core/skills.py::deploy_skills`, backed by the `templates/skills/{claude,codex}/` files above). Unlike `world.md`'s create-if-missing semantics, every deployed skill file is overwritten unconditionally on each run, since skill content is framework-owned rather than user-editable data — a newer `cac` release must always be able to propagate an update to an already-bootstrapped project, at the cost of clobbering any local hand-edit to a deployed copy.

This repo's own `.claude/skills/` and `.agents/skills/` are **deployed artifacts, not source** — never edited directly, no matter how small the change. All skill content changes are made only in the packaged templates, `templates/skills/{claude,codex}/<name>/SKILL.md`; the developer then redeploys them into this repo the same way any bootstrapped project would, by running `cac bootstrap init` (never the coding assistant, per the guardrail above). See the `skills-authored-only-in-templates` region lore. This is a maturing of the dogfooding described at the top of this file, not an end to it: this repo no longer treats its own deployed copies as a second, hand-edited source of truth alongside the templates — the templates are now the only one, exactly as they are for every other project `cac bootstrap init` targets. A skill procedure change (not just wording) must also be reflected in `docs/workflow.md` (`templates/docs/workflow.md`) in the same change — see `workflow-doc-source-of-truth`.
