---
archived: false
boss: null
created_by: John Hoff
created_on: '2026-11-21T06:18:50Z'
history: []
name: r006-reference-docstring-indent-leak
origin: c004/e002 description drift sweep
resolution: null
status: open
summary: 'core/references.py appends the identity-contract footer to a tool''s raw
  docstring without dedenting it first. Every wrapped docstring line on reference-taking
  tools therefore keeps its 4-space indent, in MCP descriptions and in CLI help (e.g.
  "Fails if it has an open encounter.     The required message..."). Likely fix: inspect.cleandoc
  the original docstring before appending.'
updated_by: John Hoff
updated_on: '2026-11-21T06:18:50Z'
---

## Observation

`packages/crypts-and-commits/src/cac/core/references.py:306` builds the wrapped function's docstring as `(function.__doc__ or "") + contract`. The original docstring's continuation lines are indented four spaces, and the appended contract line is not. Python's and Click's docstring cleaning compute the common indentation as zero and leave the continuation indentation in place. The effect:

- `cac campaign complete --help` renders "...an open encounter.     The required message ... locked     thereafter." This predates c004.
- The MCP tool descriptions of every reference-taking tool carry raw "\n    " sequences (e.g. "...call\n    again with cursor=next_cursor").

c004/e002 added a few multi-line docstrings to decorated commands (campaign set-bosses, delete; encounter assign/unassign-region, open), and these show the same artifact.

## Suggested fix

Dedent the original docstring (`inspect.cleandoc`) before appending the contract text, and add a test asserting that no rendered description or help line contains a run of interior spaces. This is a core change, outside c004's wording-only scope.
