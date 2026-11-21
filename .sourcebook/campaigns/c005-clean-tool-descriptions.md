---
archived: false
bosses:
- b007-clean-reference-tool-descriptions
created_by: John Hoff
created_on: '2026-11-21T15:45:09Z'
name: c005-clean-tool-descriptions
status: completed
updated_by: John Hoff
updated_on: '2026-11-21T16:04:33Z'
---

# c005 Clean Tool Descriptions

## Goal

Vanquish b007-clean-reference-tool-descriptions: every reference-taking MCP tool description and `cac` command help renders without stray interior whitespace, guarded by a repository-wide test.

## Tactics

- A single scripted encounter in the `crypts-and-commits` region is expected (per b007's design notes):
  1. Dedent the wrapped function's docstring (e.g. `inspect.cleandoc`) before `references.inputs` appends the identity-contract footer (`core/references.py`), leaving the contract text unchanged.
  2. Add a guard test that enumerates every registered MCP tool description and every `cac` command's help and fails on interior whitespace runs, covering decorated and undecorated tools and stating what it relies on from FastMCP/Typer cleaning.
  3. Spot-check the c004 examples (`cac campaign complete`, `set-bosses`, `delete`; `cac encounter assign-region`, `open`).
- Resolve b007's open questions with the developer while drafting the encounter, capturing answers as rulings:
  - whether the guard also covers undecorated tools' multi-line docstrings;
  - whether tailoring the shared contract footer per domain (the encounter-context sentence on boss/rumor tools) is in scope or a separate rumor.
- No behavior, signature or contract-text change; `tool-reference.md` changes only if the contract text changes (`workflow-doc-source-of-truth`). Verification follows `clean-tests-and-lint`.

## Branches

Registered on `c005-clean-tool-descriptions-assignment`; executed on `c005-clean-tool-descriptions`; integrated into `main`.

## Log

### Completed - 2026-11-21T16:04:33Z - John Hoff

Postmortem: b007 vanquished in a single scripted encounter (e001), as its design notes predicted. Measuring before drafting widened the scope usefully: 14 undecorated MCP tools leaked indentation because MCPServer passes docstrings verbatim, so the GM ruled to clean every MCP description centrally (c005-e001-clean-all-mcp-descriptions-centrally) and to tailor the contract footer per domain in this campaign rather than a rumor (c005-e001-tailor-contract-footer-per-domain), relaxing b007's contract-text-unchanged criterion for the encounter-context sentence only. Result: 0/85 MCP descriptions and 0/87 CLI commands with stray indentation (from 38 and 11), guarded by repository-wide tests that failed pre-fix; tool-reference.md documents the domain-specific footer. Independent review PASS-WITH-NOTES; all four notes addressed. pytest 1735 passed, ruff clean. Residual cosmetic: *_get docstrings keep a mid-sentence source line break ("call / again with cursor..."), which passes the guard and was left unchanged. No rumors raised; two rulings recorded for planning triage. origin/main had not moved since registration, so no logical collisions.
