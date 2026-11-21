---
archived: false
bosses:
- b007-clean-reference-tool-descriptions
created_by: John Hoff
created_on: '2026-11-21T15:45:09Z'
name: c005-clean-tool-descriptions
status: draft
updated_by: John Hoff
updated_on: '2026-11-21T15:45:09Z'
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
