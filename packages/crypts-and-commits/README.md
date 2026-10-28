# crypts-and-commits

A Coding Assistant Continuity Framework. Crypts and Commits ("CAC") uses a tabletop-gaming metaphor to describe collaboration between a developer and an AI coding assistant: the developer plays Game Master, establishing context, making decisions, and retaining final authority; the assistant plays through that context to get work done. The `cac` CLI and its `cac-mcp` MCP server are how an assistant records project context and tracks its own work across sessions, so continuity survives context resets instead of being rebuilt from scratch every time.

## Install

```bash
pip install crypts-and-commits
```

This installs the `cac` CLI and the `cac-mcp` MCP server console script.

## Quickstart

From your project's root directory, run `cac bootstrap init`. This developer-run command creates the sourcebook, registers the MCP server, and deploys three skills in Claude and Codex variants: `world-manager` for static context/lore, `world-planner` for goal planning and roadmap adoption, and `campaign-manager` for tactical selection and reviewed execution. After library upgrades the developer reruns bootstrap to redeploy framework-owned skills; agents never run it or edit deployed copies. Local instruction adoption and record migration are separate.

For the full walkthrough, see the [Quickstart guide](https://github.com/theBraindonor/crypts-and-commits/blob/main/docs/QUICKSTART.md).

Use `cac docs get branching-guide` for planning, assignment and execution branch
examples, `cac docs get tool-reference` for exact tool and command contracts, and
`cac docs get migration-guide` before upgrading an existing project.
The migration guide explains obtaining target-release guidance from verified source
or distribution when the older installed library cannot expose it, and separates
local instruction adoption from developer-run redeployment and schema migration.

## What's inside

Content is organized around **world** (project summary), **lore** (standards), **region** (documented repository path), **boss** (goal, including adopted roadmap context), **campaign** (chosen effort pursuing zero or more bosses), and **encounter** (reviewed unit of work). Optional campaign rumors preserve discoveries for later planning. Agents use the MCP server first and CLI as fallback; managed files are not edited directly. The packaged Workflow Reference Guide supplies branch, numbering, ownership, and approval procedure.

## Documentation

This package is one part of the `crypts-and-commits` development workspace — see the [project repository](https://github.com/theBraindonor/crypts-and-commits) for the full workspace. Deeper framework reference docs (e.g. the workflow guide) are available on demand via the `docs` CLI/MCP tools once your project is bootstrapped.

## License

Apache License 2.0 — see [LICENSE](https://github.com/theBraindonor/crypts-and-commits/blob/main/LICENSE).
