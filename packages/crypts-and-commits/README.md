# crypts-and-commits

A Coding Assistant Continuity Framework. Crypts and Commits ("CAC") uses a tabletop-gaming metaphor to describe collaboration between a developer and an AI coding assistant: the developer plays Game Master, establishing context, making decisions, and retaining final authority; the assistant plays through that context to get work done. The `cac` CLI and its `cac-mcp` MCP server are how an assistant records project context and tracks its own work across sessions, so continuity survives context resets instead of being rebuilt from scratch every time.

## Install

```bash
pip install crypts-and-commits
```

This installs the `cac` CLI and the `cac-mcp` MCP server console script.

## Quickstart

From your project's root directory, run `cac bootstrap init`. This one-time, developer-run command sets up everything an agent needs: it creates a `.sourcebook/` directory, registers the `crypts-and-commits` MCP server, and deploys the `world-manager` and `campaign-manager` agent skills.

For the full walkthrough, see the [Quickstart guide](https://github.com/theBraindonor/crypts-and-commits/blob/main/docs/QUICKSTART.md).

## What's inside

`.sourcebook/` content is organized around a small domain model: **world** (project-level summary), **lore** (standards and conventions), **region** (a documented path within the repository), **campaign** (a long-running initiative), and **encounter** (a concrete unit of work within a campaign). An agent typically drives this content through the `cac-mcp` MCP server; the `cac` CLI covers the same operations as a fallback for sessions where the MCP server isn't available.

## Documentation

This package is one part of the `crypts-and-commits` development workspace — see the [project repository](https://github.com/theBraindonor/crypts-and-commits) for the full workspace. Deeper framework reference docs (e.g. the workflow guide) are available on demand via the `docs` CLI/MCP tools once your project is bootstrapped.

## License

Apache License 2.0 — see [LICENSE](https://github.com/theBraindonor/crypts-and-commits/blob/main/LICENSE).
