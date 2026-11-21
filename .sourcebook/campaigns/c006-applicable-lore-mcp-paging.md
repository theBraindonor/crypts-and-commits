---
archived: false
bosses:
- b008-applicable-lore-mcp-paging
created_by: John Hoff
created_on: '2026-11-21T17:07:40Z'
name: c006-applicable-lore-mcp-paging
status: draft
updated_by: John Hoff
updated_on: '2026-11-21T17:07:40Z'
---

# c006 Applicable Lore MCP Paging

## Goal

Vanquish b008-applicable-lore-mcp-paging: `prime_applicable_lore` over MCP pages its applicable-lore set with an optional `cursor` and returns `{items, next_cursor}`, matching `cac prime applicable-lore`, with the package version bumped to 0.4.0 and migration notes segregated by release.

## Tactics

- A single scripted encounter in the `crypts-and-commits` region is expected (per b008's design notes):
  1. `mcp/prime.py`: add `cursor` and page `prime_core.applicable_lore` entries with `budget_core.paginate`, using the CLI's budget and ordering, returning `{items, next_cursor}` with no identities. Invalid cursors raise a clear error. The `references.inputs("encounter")` contract and campaign default are unchanged.
  2. Tests: MCP first page, continuation and invalid cursor; CLI parity where it's missing.
  3. Docs: `tool-reference.md` (signature table, result-shape paragraph, budget notes) and the Review steps in `planning-workflow.md` and `development-workflow.md` that call `prime_applicable_lore`.
  4. Skill templates in both the Claude and Codex flavors: world-manager (two mentions each) and the campaign-manager reviewer prompt, so agents follow `next_cursor`. Deployed copies are redeployed by the developer.
  5. Version: bump `version` to 0.4.0 in the root, `crypts-and-commits` and `demo-api` `pyproject.toml` files only; refresh `pdm.lock` only if PDM reports it stale. No CHANGELOG, tag or release, and the schema stays at 1.
  6. `migration-guide.md`: add a release-labeled 0.4.0 subsection under "Version-specific migrations" with b008's note, and move existing post-0.3.0 notes (c002 rulings) into it with their content unchanged.
- Verification follows `clean-tests-and-lint`; documentation follows `workflow-doc-source-of-truth` and `skills-authored-only-in-templates`.

## Branches

Registered on `c006-applicable-lore-mcp-paging-assignment`; executed on `c006-applicable-lore-mcp-paging`; integrated into `main`.
