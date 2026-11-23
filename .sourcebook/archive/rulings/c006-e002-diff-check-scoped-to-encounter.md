---
archived: true
campaign: c006-applicable-lore-mcp-paging
created_by: John Hoff
created_on: '2026-11-23T17:05:30Z'
encounter: e002-demo-api-literal-priming
history:
- action: note
  by: John Hoff
  message: No world change needed. This only scoped one encounter's Verification diff
    check (c006/e002) to its own files while e001's uncommitted work was on the same
    branch, and it was applied and satisfied there. It sets no lasting convention
    for lore, regions or the world summary. Triaged on planning, 2026-11-23, with
    the developer.
  'on': '2026-11-23T18:13:02Z'
name: c006-e002-diff-check-scoped-to-encounter
origin: John Hoff (developer/GM), approving e002 open after independent review note
  3, 2026-11-23
resolution: No world change needed. This only scoped one encounter's Verification
  diff check (c006/e002) to its own files while e001's uncommitted work was on the
  same branch, and it was applied and satisfied there. It sets no lasting convention
  for lore, regions or the world summary. Triaged on planning, 2026-11-23, with the
  developer.
status: noted
summary: e002's Verification check "git diff touches only graph.py and test_graph.py"
  is scoped to e002's own changes, not the whole branch. Within packages/demo-api
  only src/demo_api/chat/graph.py and tests/test_graph.py change, apart from e001's
  uncommitted demo-api pyproject.toml version bump. e001's uncommitted work elsewhere
  on the branch is excluded.
updated_by: John Hoff
updated_on: '2026-11-23T18:14:41Z'
---

## Decision

Scope c006/e002's Verification check "`git diff` touches only `packages/demo-api/src/demo_api/chat/graph.py` and `packages/demo-api/tests/test_graph.py`" to e002's own changes. Within `packages/demo-api`, only those two files change, apart from the uncommitted `packages/demo-api/pyproject.toml` 0.4.0 version bump, which belongs to e001. e001's uncommitted work elsewhere on the branch is excluded.

## Context

The independent review of e002 (PASS-WITH-NOTES, note 3) observed that the check could not hold literally: the c006 execution branch carries e001's uncommitted changes (prime, docs, skill templates, pyproject bumps) while e002 runs. e002's body was already locked by the review, so the clarification was recorded as an encounter log message and approved by the developer when opening e002.

## Consequences

- e002's diff-scope verification is judged against the demo-api files only, with the e001 pyproject bump excluded.
- No lore, region or world change is implied; this is an execution-scope clarification for one encounter.
