---
archived: false
campaign: c005-clean-tool-descriptions
created_by: John Hoff
created_on: '2026-11-21T15:52:00Z'
encounter: e001-clean-tool-descriptions
history: []
name: c005-e001-clean-all-mcp-descriptions-centrally
origin: John Hoff (GM), answering b007's open question while drafting c005/e001
resolution: null
status: recorded
summary: The description guard covers every MCP tool and CLI command, not only reference-decorated
  ones; the 14 undecorated MCP tools whose descriptions leak indentation (MCPServer
  does not clean docstrings) are fixed centrally at registration in mcp/instance.py
  rather than per tool module or deferred to a rumor.
updated_by: John Hoff
updated_on: '2026-11-21T15:52:00Z'
---

## Decision

Clean every MCP tool description centrally when it is registered (in `mcp/instance.py`), and have the guard test cover all registered MCP tools and all `cac` commands, decorated or not.

## Context

b007 asked whether the guard should cover undecorated tools' multi-line docstrings, assuming FastMCP/Typer might already clean them. Measurement on c005 showed Typer does clean undecorated CLI help (all 11 CLI leaks are decorated), but the MCP SDK (`MCPServer`, mcp 2.3.0) does not: 14 undecorated MCP tools (`docs_*`, `index_*`, `world_*`, `lore_*`, `region_*`, `prime_get`) leak indentation alongside the 24 decorated ones. The alternative, fixing only `references.inputs` and capturing the undecorated leaks as a rumor, was declined.

## Consequences

- Scope grows slightly past b007's literal "reference-taking tools" summary, within its "every tool" success criterion.
- Tool modules stay untouched; future tools are cleaned automatically, and the guard catches regressions on both surfaces.
