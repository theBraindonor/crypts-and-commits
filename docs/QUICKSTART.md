# Quickstart

Get Crypts and Commits (CAC) working in your own project in three steps.
This guide only covers getting an agent session up and running - once it is,
your coding assistant already knows the rest (its `world-manager` and
`campaign-manager` skills, and the `docs` MCP/CLI tool for deeper reference,
are all deployed for you by the last step below).

## 1. Install the package

`crypts-and-commits` isn't published to PyPI yet, so install it straight from
this repository:

```bash
pip install "git+https://github.com/theBraindonor/crypts-and-commits.git#subdirectory=packages/crypts-and-commits"
```

This installs the `cac` CLI and the `cac-mcp` MCP server console script.

## 2. Bootstrap your project

From your project's root directory:

```bash
cac bootstrap init
```

This is a one-time, developer-run command (never run it from inside an agent
session) that sets up everything an agent needs:

- Creates `.sourcebook/` and seeds an empty `world.md`.
- Registers the `crypts-and-commits` MCP server for both Claude Code
  (`.mcp.json`) and Codex (`.codex/config.toml`), and deploys the Codex
  sourcebook-guard hook.
- Adds the `.sourcebook/` guardrail permissions to `.claude/settings.json`.
- Deploys the `world-manager` and `campaign-manager` agent skills into both
  `.claude/skills/` and `.agents/skills/`.

It's safe to run again later - re-running only fills in anything missing or
updates framework-owned files (like the skills) to a newer `cac` release;
your own edits to `.sourcebook/` content are never touched.

## 3. Hand off to your agent

Start a session with your coding assistant and ask it to flesh out the world
file - for example:

> Use the world-manager skill to help me write our world summary.

From here, your agent drives `.sourcebook/` for you: building out lore,
regions, and campaigns as work comes up. If you (or your agent) ever need the
full domain-model reference, it's one call away - `cac docs get workflow`, or
ask the agent to look it up.
