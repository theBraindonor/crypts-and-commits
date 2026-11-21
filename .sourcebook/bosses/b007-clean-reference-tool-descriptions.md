---
archived: false
created_by: John Hoff
created_on: '2026-11-21T06:27:06Z'
depends_on: []
name: b007-clean-reference-tool-descriptions
status: available
summary: Fix the stray indentation in descriptions of reference-taking tools. core/references.py:306
  appends the identity-contract footer to the raw docstring without dedenting, so
  every wrapped line keeps its 4-space indent in MCP tool descriptions and CLI help
  ("...open encounter.     The required message..."). Dedent before appending, and
  add a guard test across all tools and commands.
updated_by: John Hoff
updated_on: '2026-11-21T06:28:09Z'
---

## Goal

Make every reference-taking tool's description render cleanly: no stray interior whitespace in MCP tool descriptions or `cac` CLI help, regardless of how the source docstring wraps.

## Rationale

`packages/crypts-and-commits/src/cac/core/references.py:306` builds the wrapped function's docstring as `(function.__doc__ or "") + contract`. The source docstring's continuation lines are indented four spaces, and the appended contract (it starts with `\n` and has no indent) leaves the common indentation at zero. Docstring cleaning therefore keeps the continuation indent:

- `cac campaign complete --help` renders "...Fails if it has an open encounter.     The required message ... locked     thereafter." This predates c004.
- MCP descriptions of reference-taking tools carry raw `\n    ` runs (e.g. "...call\n    again with cursor=next_cursor").
- `cli/common.py`'s CLI wrapper copies `adapted.__doc__`, so CLI and MCP inherit the same defect.

Agents read these descriptions on every call. c004 made their content accurate; this goal makes them render cleanly. Raised as r006 during c004/e002.

## Success Criteria

- The `references.inputs` decorator dedents the original docstring (e.g. `inspect.cleandoc`) before appending the contract text, so the combined docstring has consistent indentation. The contract text and its content are unchanged.
- A guard test enumerates every registered MCP tool description and every `cac` command's help and fails on interior whitespace runs (e.g. two or more spaces after non-space text, or a newline followed by indentation inside a paragraph), covering both decorated and undecorated tools.
- Rendered help for the c004 examples (`cac campaign complete`, `set-bosses`, `delete`; `cac encounter assign-region`, `open`) shows no stray spaces.
- No behavior, signature or contract-text change; `tool-reference.md` needs no update unless the contract text itself changes (`workflow-doc-source-of-truth`).
- `pdm run pytest -q` and ruff are clean.

## Design Notes

Promoted from r006-reference-docstring-indent-leak during planning on 2026-11-21. The fix is expected to be a small core change plus a repository-wide guard test, so it should suit a single encounter.

## Open Questions

- Should the guard also cover undecorated tools' multi-line docstrings? FastMCP and Typer may already clean them; the test should state what it relies on.
- The shared contract footer includes "Qualified encounter context overrides active fallback..." even on boss and rumor tools, where encounter context does not apply (noted, but not changed, in c004/e002). Is tailoring the footer per domain in scope here, or a separate rumor?
