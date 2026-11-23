---
archived: false
campaign: c006-applicable-lore-mcp-paging
created_by: John Hoff
created_on: '2026-11-21T17:10:01Z'
depends_on: []
kind: scripted
name: e001-applicable-lore-mcp-paging
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-11-23T17:31:10Z'
---

## Requirements

Vanquish b008-applicable-lore-mcp-paging. Revised after the first independent review (REJECT) per ruling c006-e001-json-measured-applicable-lore-paging.

1. `prime_applicable_lore(encounter, campaign=None, cursor=None)` (`packages/crypts-and-commits/src/cac/mcp/prime.py`) returns `{"items": [{name, summary, ref}, ...], "next_cursor": str | None}`. There is no `identities` array. The `references.inputs("encounter")` contract, the campaign default and `prime_core.applicable_lore` are unchanged.
2. **JSON-measured paging, shared by both surfaces:** a new helper in `core/prime.py` (e.g. `page_applicable_lore(entries, cursor) -> budget_core.Page`) pages the entries with `budget_core.paginate`:
   - it measures each item as the compact JSON of `{name, summary, ref}` (`references.encoded`);
   - its budget is `config.RESPONSE_BUDGET` minus the compact JSON of the envelope `{"items": [], "next_cursor": "<len(entries)>"}`, so every page, envelope included, fits the response budget.

   `mcp/prime.py` and `cli/prime.py` both call it, so their page breaks are identical. The CLI still prints its existing text lines and `--cursor` hint from the page's items.
3. **Cursor validation:** an invalid or out-of-range cursor raises `budget_core.InvalidCursorError` on MCP (as `lore_list` does) and fails with that message on the CLI, including when no lore applies. The CLI pages before printing "No applicable enabled lore was found for this encounter.", so a stale cursor is never silently accepted. A missing cursor on an empty set returns `{items: [], next_cursor: null}` on MCP, and the CLI keeps its existing message.
4. Tests: MCP covers the new shape on existing cases; multi-page continuation under a reduced `config.RESPONSE_BUDGET`, asserting each page's compact JSON fits that budget; and an invalid cursor on both a non-empty and an empty set. CLI covers continuation under the same reduced budget with the same page breaks as MCP, and an invalid cursor on a non-empty and an empty set. Core covers the helper's budget arithmetic.
5. `packages/crypts-and-commits/src/cac/core/templates/docs/tool-reference.md`:
   - the Prime table row becomes `prime_applicable_lore(encounter, campaign=None, cursor=None)`;
   - the closing Prime paragraph documents `{items, next_cursor}` (no identities), continuation, and that pages are measured on the compact JSON of items plus envelope, identically for MCP and CLI;
   - the identities paragraph (around line 92, "`prime_applicable_lore` keeps its lore-entry shape") says its items keep the lore-entry shape with no identities;
   - the selector table row (around line 163) adds `cursor` to its literal inputs;
   - the "Paged lists" sentence in §Response budgets and continuation (around line 64) names `prime_applicable_lore` alongside `*_list`, `boss_candidates` and `docs_list`.
6. `planning-workflow.md` and `development-workflow.md` Review steps (step 3, "Review with `prime_applicable_lore`...") say to follow `next_cursor` until it's null before hydrating bodies. The wording is identical in both, as a synchronized shared rule.
7. Skill templates under `packages/crypts-and-commits/src/cac/core/templates/skills/`, Claude and Codex flavors:
   - `world_manager/SKILL.md`, both mentions: replace "The MCP tool returns the whole set in one list (no cursor)..." with paging that matches the CLI (pass `cursor=next_cursor` until it's null), and make step 3 "Review a plan" collect every page.
   - `campaign_manager/SKILL.md` reviewer prompt template: the `prime_applicable_lore` bullet tells the reviewer to follow `next_cursor` (MCP) / `--cursor` (CLI) until exhausted.
   - The two flavors stay functionally equivalent. Deployed copies under `.claude/skills/` and `.agents/skills/` are not edited; the developer redeploys them.
8. Version: `version = "0.3.0"` becomes `"0.4.0"` in the repository root `pyproject.toml`, `packages/crypts-and-commits/pyproject.toml` and `packages/demo-api/pyproject.toml`. `pdm.lock` changes only if `pdm lock --check` reports it stale after the bump, in which case it is regenerated with `pdm lock`. Not touched: `packages/demo-ui/package.json` and its lock, `docs/CHANGELOG.md`, tags and releases. `SOURCEBOOK_SCHEMA_VERSION` stays 1.
9. `migration-guide.md` "Version-specific migrations": migration details are segregated by release, newest first. A new `### Upgrading from 0.3.0 to 0.4.0` subsection opens the section and holds:
   - the existing "Rulings are additive within schema version 1..." paragraph (c002), moved verbatim;
   - a new b008 paragraph: within schema 1, `prime_applicable_lore`'s MCP result changes from a bare list to `{items, next_cursor}` with an optional `cursor`, and `cac prime applicable-lore` pages break at JSON-measured boundaries; no record migration, schema bump, guardrail suspension or bootstrap migration is needed; update MCP consumers with the library; the developer redeploys skills with `cac bootstrap init` so agents follow `next_cursor`.

   A `### Boss Edition (0.3.0)` heading is inserted above the existing Boss Edition paragraphs ("Boss planning storage is additive...", "Within prerelease Boss Edition..."). Their text and the existing `### Adopt an existing roadmap` subsection are unchanged.
10. Tool descriptions stay clean prose (c005 guards) and consistent across MCP and CLI: the MCP docstring states paging and `next_cursor` like the CLI help.

## Rationale

`cli-mcp-parity` requires paginated list commands to expose the same cursor paging over MCP; `prime_applicable_lore` is the one list-shaped MCP read that doesn't, so a large applicable-lore set could exceed the response budget. The first review showed that sizing pages by the CLI's text line still allows a JSON page over budget, so measurement is on compact JSON plus envelope. Doing it in one core helper keeps both wrappers thin and their page breaks identical. The result-shape change is breaking for MCP consumers, so the developer chose (b008 planning, 2026-11-21) a 0.4.0 pyproject bump, a release-labeled migration-guide subsection, and segregation of post-0.3.0 notes from Boss Edition notes, with the CHANGELOG, tag and release left for later. Docs and skills must move in the same change (`workflow-doc-source-of-truth`, `skills-authored-only-in-templates`), including the reviewer prompt, which otherwise silently reads only the first page.

## Plan

1. Write the failing tests first (Requirement 4), using a monkeypatched small `config.RESPONSE_BUDGET` to force multiple pages. Confirm the new MCP, CLI-paging-boundary and core-helper tests fail before step 2.
2. `core/prime.py`: add `page_applicable_lore(entries, cursor)` per Requirement 2, plus a small `applicable_lore_item(entry) -> dict` used for both measurement and the MCP items.
3. `mcp/prime.py`: add `cursor: str | None = None`, call the helper and return `{"items": [...], "next_cursor": page.next_cursor}`. Update the docstring to describe paging and `next_cursor`.
4. `cli/prime.py`: replace its inline `budget_core.paginate(..., render=...)` with the helper, paging before the empty-set message per Requirement 3. Output format is otherwise unchanged.
5. `tool-reference.md` edits per Requirement 5.
6. Workflow guides' Review step per Requirement 6.
7. Skill templates per Requirement 7 (four files).
8. Version bump per Requirement 8: edit the three `pyproject.toml` files, run `pdm lock --check`, and regenerate only if it reports stale.
9. Migration guide per Requirement 9.
10. Run the whole suite and ruff; spot-check against this repo with a direct Python call to `mcp_prime.prime_applicable_lore` on this encounter, plus `cac prime applicable-lore e001 -c c006`.

## Verification

- New tests fail before steps 2-4 and pass afterwards. Under a reduced budget, MCP and CLI break pages at the same entries, and each MCP page's compact JSON is at most the budget.
- An out-of-range cursor fails on both surfaces for empty and non-empty sets.
- A direct call returns `{items, next_cursor: None}` for this encounter, with the same entries the CLI prints.
- `grep` across `packages/crypts-and-commits/src/cac/core/templates` finds no remaining claim that `prime_applicable_lore` has no cursor or returns a list.
- The three `pyproject.toml` files read 0.4.0; `demo-ui` and `CHANGELOG.md` are unchanged; `pdm lock --check` passes.
- The migration guide's Version-specific section opens with the 0.4.0 subsection holding the moved rulings paragraph (verbatim) and the b008 note, followed by the Boss Edition (0.3.0) heading.
- Per `clean-tests-and-lint`: `pdm run pytest -q` passes (including the c005 description guards), `pdm run ruff check .` reports zero errors, and `pdm run ruff format .` produces no diffs.

## Log

### Review - 2026-11-21T17:17:33Z - John Hoff

Independent review PASS-WITH-NOTES against clean-tests-and-lint, cli-mcp-parity, console-best-practices, skills-authored-only-in-templates and workflow-doc-source-of-truth. The revision resolves the prior REJECT per ruling c006-e001-json-measured-applicable-lore-paging. A single core/prime.py helper pages {name, summary, ref} items measured as compact JSON against RESPONSE_BUDGET minus the compact {items, next_cursor} envelope; the per-item +1 charge covers the null-versus-short-cursor difference. Thin MCP and CLI wrappers share identical page breaks, and cursor validation (including on an empty set) matches lore_list. The MCP result becomes structured {items, next_cursor}, and descriptions align with tool-reference.md. The Plan updates tool-reference.md (paged-lists sentence, identities paragraph, selector and Prime table rows, closing paragraph), both phase guides' Review step 3 with identical synchronized wording, and all four skill templates in both flavors (template paths only; the developer redeploys), and adds a release-labeled 0.4.0 migration subsection. Tests-first and the pytest/ruff gates are in Verification. Notes: paginate always admits one item, so a single oversized entry can still exceed the budget, and the documented "every page fits" claim should carry that exception. Consider documenting the new newest-first, per-release segregation convention under "Maintaining this guide". Filing the c002 rulings paragraph under 0.3.0 to 0.4.0 rests on developer-confirmed release history that was not verified here.

### Message - 2026-11-21T17:18:16Z - John Hoff

Developer-approved handling of review notes before opening: (1) tool-reference.md will state that every applicable-lore page fits the response budget except a single entry that alone exceeds it (paginate always admits one item), rather than an absolute guarantee; Requirement 2's "every page fits" is read with that exception. (2) migration-guide.md's "Maintaining this guide" section gains one sentence recording the new convention: version-specific notes are grouped under one release-labeled subsection per release, newest first. (3) Verified release history: c002's merge 498f17b is after the v0.3.0 tag and not contained in it, so the rulings paragraph belongs in the 0.3.0 to 0.4.0 subsection.

### Message - 2026-11-21T17:22:51Z - John Hoff

Deviation (developer-approved, ruling c006-e001-applicable-lore-keeps-encounter-identity): Requirement 1's result shape becomes {items, next_cursor, identity}. references.inputs adds the selected encounter's identity to dict results after paging, which the plan did not anticipate; a new test caught an over-budget page (487 > 400). page_applicable_lore now also takes that identity and reserves it in its envelope; MCP and CLI both pass it, keeping page breaks identical and pages within budget. tool-reference.md will document the identity field (Requirement 5's closing Prime paragraph and identities paragraph). Still no per-item identities array.

### Message - 2026-11-21T17:28:11Z - John Hoff

Implementation done; verification blocked. All e001 steps are implemented: core paging helper (JSON-measured, reserving the encounter identity), MCP/CLI wrappers, tests (8 failed pre-fix, all pass after), tool-reference.md, both workflow guides' Review step, four skill templates, pyproject 0.4.0 bumps (pdm lock --check passes, so pdm.lock is unchanged), and the migration guide's 0.4.0 subsection (rulings paragraph verified verbatim) with the Boss Edition (0.3.0) heading and the Maintaining-this-guide convention sentence. Stale-claim grep is clean; demo-ui, CHANGELOG.md and deployed skills are untouched; ruff check and format are clean; direct MCP call and CLI agree on the 5 entries for this encounter. The full suite reports 1738 passed and 4 failed: demo-api chat tests fail because demo-api passes live sourcebook priming (c006's campaign body contains `{items, next_cursor}`) into ChatPromptTemplate unescaped. That is a pre-existing demo-api bug, handled per ruling c006-e001-demo-api-brace-fix-as-e002 in a new encounter c006/e002. e001 stays open until the suite is green.

### Completed - 2026-11-23T17:31:10Z - John Hoff

Completed with developer confirmation. The verification blocker is cleared: with c006/e002's demo-api literal-priming fix in place, the full `pdm run pytest -q` reports 1743 passed and 0 failed, `ruff check .` passes, and `ruff format --check .` reports no changes. All other e001 verification items were confirmed earlier, as recorded in the implementation message.
