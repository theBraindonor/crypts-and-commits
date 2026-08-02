---
archived: true
campaign: v0.1.1-mcp-transition
created_by: John Hoff
created_on: '2026-07-25T21:56:41Z'
depends_on: []
name: rename-mcp-server-to-crypts-and-commits
regions: []
status: completed
updated_by: John Hoff
updated_on: '2026-08-02T22:11:30Z'
---

# Encounter

## Requirements

- The MCP server's registered name must change from `cac` to `crypts-and-commits`
  everywhere that name is meaningful, so the tool-call prefix an agent session
  sees changes from `mcp__cac__*` to `mcp__crypts-and-commits__*`:
  - `FastMCP("cac")` in `mcp/instance.py`.
  - `MCP_SERVER_NAME = "cac"` in `core/config.py` (the constant `initialize_mcp_config`
    uses as the `.mcp.json` `mcpServers` key).
  - This repo's own `.mcp.json` — rename the `cac` key to `crypts-and-commits`
    (a plain repo-root file, not `.sourcebook/`, so a direct edit is fine).
  - This repo's own `.claude/settings.json` (`permissions.allow: ["mcp__cac"]` →
    `["mcp__crypts-and-commits"]`) and `.claude/settings.local.json`
    (`enabledMcpjsonServers: ["cac"]` → `["crypts-and-commits"]`).
  - Every `mcp__cac__<tool>` reference in `.claude/skills/world-manager/SKILL.md`
    and `.claude/skills/campaign-manager/SKILL.md` (including each file's
    `allowed-tools` frontmatter), rewritten to `mcp__crypts-and-commits__<tool>`.
  - The two `.agents/skills/*/SKILL.md` mirrors' prose ("registered as `cac`" and
    "the `mcp__cac__`-prefixed form") — bare Codex tool names themselves (e.g.
    `world_get`) are unaffected since they carry no server prefix.
  - `CLAUDE.md`'s two literal mentions ("the `cac` MCP server's tools" and
    "Claude Code's `mcp__cac__`-prefixed form") and `AGENTS.md`'s "registered as
    `cac` per `.mcp.json`".
  - `cli/bootstrap.py`'s `_report_mcp_config` user-facing strings ("Registered
    the cac MCP server..." / "...already registers the cac MCP server") and
    `core/bootstrap.py`'s docstring mention.
  - Existing assertions in `tests/core/test_bootstrap.py` and
    `tests/cli/test_bootstrap.py` that check for the literal `"cac"` key in a
    generated `.mcp.json`.
- Explicitly out of scope: the `cac` Python package name, the `cac` console
  script/CLI command, the `cac-mcp` executable filename
  (`CAC_MCP_SCRIPT_NAME`), and the Typer app's own `name="cac"` in `cli/app.py`
  — the user confirmed "cac" remains fine as the CLI's own abbreviation; only
  the MCP server's registered name (and everything that echoes it back as a
  tool-call prefix) is changing.
- No behavior change beyond the renamed string — `initialize_mcp_config`'s
  merge/idempotency semantics, and every tool's actual operation, stay the
  same.

## Rationale

Seeing `mcp__cac__*` tool calls narrated in a Claude Code session (e.g. "calling
cac") reads as if the assistant is invoking a completely different tool called
"cac", separate from the project itself, rather than this project's own MCP
server. Renaming the server's registered name to `crypts-and-commits` makes
the tool-call prefix self-evidently belong to this project. The `cac`
abbreviation stays appropriate for the CLI, where a short command name is
expected and the context is unambiguous.

## Plan

1. `core/config.py`: change `MCP_SERVER_NAME = "cac"` to
   `MCP_SERVER_NAME = "crypts-and-commits"`.
2. `mcp/instance.py`: change `FastMCP("cac")` to `FastMCP("crypts-and-commits")`.
3. `core/bootstrap.py` / `cli/bootstrap.py`: update the docstring and the two
   `_report_mcp_config` message strings to say `crypts-and-commits` instead of
   `cac` where they name the MCP server.
4. Update `tests/core/test_bootstrap.py` and `tests/cli/test_bootstrap.py`:
   replace the literal `"cac"` key lookups/assertions against generated
   `.mcp.json` content with `"crypts-and-commits"`.
5. Update this repo's own `.mcp.json`: rename the `cac` entry under
   `mcpServers` to `crypts-and-commits` (same command/args value).
6. Update this repo's own `.claude/settings.json`
   (`mcp__cac` → `mcp__crypts-and-commits` in `permissions.allow`) and
   `.claude/settings.local.json` (`enabledMcpjsonServers` entry `cac` →
   `crypts-and-commits`).
7. Update `.claude/skills/world-manager/SKILL.md` and
   `.claude/skills/campaign-manager/SKILL.md`: replace every `mcp__cac__`
   occurrence (body text and `allowed-tools` frontmatter) with
   `mcp__crypts-and-commits__`.
8. Update `.agents/skills/world-manager/SKILL.md` and
   `.agents/skills/campaign-manager/SKILL.md`: update the "registered as `cac`"
   / "`mcp__cac__`-prefixed form" prose to name `crypts-and-commits`.
9. Update `CLAUDE.md` (the two literal mentions noted above) and `AGENTS.md`
   ("registered as `cac` per `.mcp.json`").
10. Restart/reconnect the MCP server for this session (the harness picks up
    `.mcp.json` changes on reconnect, not mid-session) and confirm tools are
    reachable under the new `mcp__crypts-and-commits__*` prefix.

## Verification

- `pdm run pytest -q` passes; `pdm run ruff check .` and `pdm run ruff format .`
  are clean, per the `clean-tests-and-lint` world lore.
- `Grep` for `mcp__cac` and for a literal `"cac"` `.mcp.json`/`mcpServers` key
  across the repo (excluding historical `.sourcebook/encounters/**` records,
  which are locked and out of scope) returns no hits outside the intentionally
  unchanged CLI-name references (`cac` package, `cac` console command,
  `cac-mcp` executable, Typer app `name="cac"`).
- After reconnecting the MCP server, a live call such as
  `mcp__crypts-and-commits__world_get()` succeeds, confirming the new prefix is
  live end-to-end (config → server → harness).

## Log

### Review - 2026-07-25T22:00:16Z - John Hoff

Reviewed against the single applicable lore item, clean-tests-and-lint (world-assigned; no regions are attached to this encounter) — honored: the Verification section explicitly gates on `pdm run pytest -q`, `pdm run ruff check .`, and `pdm run ruff format .`, with no skip/suppression shortcuts proposed. Two minor completeness gaps were found by reading the files the Plan itself names, not lore conflicts: (1) the allowed-tools frontmatter in both .claude/skills/*/SKILL.md files uses a bare `mcp__cac` permission scope (no trailing double underscore), which a literal search for the `mcp__cac__` substring described in Plan step 7 would not catch, despite the Requirements correctly calling out that this frontmatter needs updating; (2) the descriptive phrase "the cac MCP server" appears in AGENTS.md and both .agents/skills/*/SKILL.md files but, unlike its treatment in CLAUDE.md, is not explicitly enumerated for rename there — only the adjacent "registered as cac" substring is — so as literally specified it could survive the rename and wouldn't be caught by the Verification grep either. Neither gap conflicts with lore; both are worth a deliberate check during execution rather than trusting the literal enumerated substrings.

### Completed - 2026-07-25T22:05:16Z - John Hoff

pdm run pytest -q: 563 passed. ruff check/format: clean. Confirmed live end-to-end after restarting Claude Code: a mcp__crypts-and-commits__world_get() call succeeded under the new prefix, and the old mcp__cac__* tools are gone from the session's tool list.
