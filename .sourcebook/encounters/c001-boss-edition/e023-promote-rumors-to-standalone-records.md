---
archived: false
campaign: c001-boss-edition
created_by: John Hoff
created_on: '2026-10-28T14:36:05Z'
depends_on:
- e021-sync-public-docs-with-boss-edition
kind: scripted
name: e023-promote-rumors-to-standalone-records
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-10-28T15:46:28Z'
---

## Requirements

Replace the unreleased per-campaign rumors document (`.sourcebook/bosses/rumors/<campaign>.md`, e011) with **rumors as standalone, numbered backlog records**: "we think X should be done" notes that can come from anywhere and that planning later links to bosses. Rumors are unreleased Boss Edition content, and this repository has no rumors records (`cac rumors list` is empty), so the old model is **removed outright**: no compatibility layer, no migration, no deprecation. Code, both skill flavors' rumor procedure, and both owning docs change together in this one encounter, so no part of the branch is ever internally inconsistent.

Developer-agreed design (2026-10-28):

1. **Storage and naming.** One file per rumor at `.sourcebook/rumors/<name>.md`. Archived rumors go to `.sourcebook/archive/rumors/`. Numbered names are `rNNN-slug`, with short ref `rNNN`, resolved through `core/references.py` like `bNNN` (exact canonical names win, archived records participate, duplicates are ambiguous). Create names are literal. Skills allocate numbers; core never does.
2. **Fields.** Frontmatter:
   - `name` and `status`.
   - A required `summary` (at most 500 characters, validated as for bosses).
   - A required nonblank free-text `origin`: who or what raised the rumor, in any words (a campaign, a review, a customer, the running project). It is deliberately **not** validated against repository records.
   - `boss`: null unless promoted.
   - `resolution`: null, or the current promote/dismiss message.
   - `history`: an append-only list of `{action, message, by, on}` entries, one per promote, dismiss and reopen. It records every transition message, including reopen messages, and `rumor_update` never touches it.
   - `archived`, plus `created_by`/`created_on`/`updated_by`/`updated_on`.

   The body is freeform markdown and may be empty.
3. **Lifecycle.** `open` → `promoted` (linked to a boss; message optional) or `dismissed` (reason required). `reopen` (message required) returns a promoted or dismissed, unarchived rumor to `open`, clearing `boss` and `resolution`; `history` keeps the earlier entries. `archive` accepts only promoted or dismissed rumors and moves the record to `archive/rumors/`; archived names stay reserved and readable. There is no delete. Dismissal covers unwanted rumors, and retaining records keeps number allocation sound.
4. **Two-step promotion.** Bosses are created through the existing boss tools. `rumor_promote(name, boss, message=None)` then links an `open` rumor to an existing **unassigned `proposed` or `available`** boss. That boss may already exist from planning, and several rumors may link to the same boss. The link is recorded **only on the rumor**, not back on the boss (like encounter-to-region links). So promotion never touches a boss record and never conflicts with frozen boss designs. A boss's rumors are found by listing or searching rumors. Promotion is meant to happen on the planning branch; that is skill guidance, and the endpoint stays branch-agnostic.
5. **Editing.** `rumor_update(name, body, summary, origin)` is a **full replacement** of those three fields together, like `boss_update`. It is allowed only while the rumor is `open`. Promoted and dismissed rumors are read-only until reopened.
6. **Collisions and renumbering.** Capture is allowed on any branch, and number collisions are accepted and resolved on the planning branch. `rumor_renumber(name, new_name)` renames a live (unarchived) rumor whose status is `open` or `dismissed` to an unused literal name. It updates the file name, `name` and index row, and leaves every other field unchanged. **Promoted rumors cannot be renumbered.** Promotion happens on planning, so their numbers are already settled there. Archived rumors are never renumbered. Reopening a promoted rumor makes it renumberable again.
7. **No dedupe.** Similar or duplicate rumors are allowed; repetition is a signal. No uniqueness check beyond the name.
8. **Listing and search.** `rumor_list(cursor=None, include_archived=False, status=None)` returns canonical names with parallel identities through `references.identity_page`, which uses the shared `budget.paginate` cursor contract. It can be filtered by status, and a status outside `RUMOR_STATUSES` is an error. `rumor_get(name, cursor=None)` returns metadata and a body continued through the shared `budget.fit_response` contract (via `references.inputs`). Rumors get their own search object type, `rumor`, which the managed writes index and recover like bosses. Rumors were never indexed under the old model, so the index snapshot `VERSION` stays `"1"`, and an existing index stays fresh across the upgrade. Rumors are **not** added to `prime_get`.
9. **Interfaces (per `cli-mcp-parity`).**
   - A singular `rumor` domain matches `boss`.
   - Exactly nine MCP tools: `rumor_list`, `rumor_get`, `rumor_create(name, body, summary, origin)`, `rumor_update(name, body, summary, origin)`, `rumor_promote(name, boss, message=None)`, `rumor_dismiss(name, message)`, `rumor_reopen(name, message)`, `rumor_archive(name)`, `rumor_renumber(name, new_name)`. On MCP, `body`, `summary` and `origin` are required strings for both create and update; that is where the CLI uses an editor fallback.
   - Exactly nine CLI commands: `cac rumor list|get|create|update|promote|dismiss|reopen|archive|renumber`. `create`/`update` take `--body`/`--body-file` (editor fallback when neither is given) plus required `--summary`/`-s` and `--origin`/`-o`. `promote`/`dismiss`/`reopen` take `--message`/`-m`, which is required for dismiss and reopen.
   - The old `rumors_*` tools, the `cac rumors` group and the `bosses/rumors/` storage are removed.
   - All CLI output of stored content (body, summary, origin, resolution, history) prints with `markup=False` (`console-best-practices`).
10. **Owning docs in the same change (per `workflow-doc-source-of-truth`).** Rewrite **every** rumor statement in `templates/docs/workflow.md`: the domain overview (around line 43), the branch-settings table (line 81), the archive layout (line 264), the "Campaign rumors" section (lines 416-431), the skill-responsibility list (line 557) and the agent-procedure text (lines 677-683). The procedure becomes: capture rumors from any skill on any branch; on planning, triage open rumors, renumber collisions, promote to bosses or dismiss, and archive. In `templates/docs/tool-reference.md`, replace the rumors contracts with the nine tools and commands, their arguments, results and errors.
11. **Skill templates (per `skills-authored-only-in-templates`).** In both flavors (`templates/skills/{claude,codex}/`), replace every rumors reference in `world_planner/SKILL.md` and `campaign_manager/SKILL.md` with the new procedure, using `rumor_*` tool names. world-planner owns triage, renumbering, promotion, dismissal and archiving on planning. campaign-manager captures rumors during execution without expanding scope. Add a one-line capture pointer to `world_manager/SKILL.md` if it mentions discoveries. Keep the two flavors identical apart from tool-name prefixes. Update the `test_skills.py` tool-name regex (line 68) from `rumors` to `rumor`, so it keeps proving that every tool the templates call is registered. Never edit deployed copies; the developer redeploys with `cac bootstrap init`.

Out of scope (later encounters in this campaign): `branching-guide.md` and `migration-guide.md` (e024); this repo's `CLAUDE.md`/`AGENTS.md` and the `crypts-and-commits` region summary, which still name `bosses/rumors/` and `rumors.py` but are not owning docs under the lore (e024); the public docs (`README.md`, `docs/QUICKSTART.md`, package README) and `docs/CHANGELOG.md` (e025); running `cac bootstrap init` or `cac index rebuild` in any directory (developer-only).

## Rationale

The per-campaign document made rumors a strict output of execution. Most good "we should do X" ideas arrive from elsewhere: operating the project, reviews, other people. Each one needs its own identity so that planning can triage it, link it to a goal, dismiss it with a reason, or count how often it recurs. Numbered standalone records give exactly that, and promotion becomes the explicit bridge from backlog to boss. Keeping the link on the rumor only keeps boss design freezing and campaign coupling simple. Freezing the number at promotion makes planning the single place where rumor numbering is settled. A frontmatter `history` keeps every transition message, because a body `## Log` would be lost on a full-body update. Code, skills and owning docs change together because `test_skills.py` checks template tool names against the registered tools, and the lore requires owning docs to change in the same change. Doing this before the c001 PR, while rumors are still unreleased, avoids shipping a model that would immediately need a schema migration.

## Plan

1. Confirm branch `c001-boss-edition` and a clean working tree.
2. `core/config.py`: add `RUMOR_DIR_NAME = "rumors"` at the sourcebook root, `RUMOR_STATUSES = ("open", "promoted", "dismissed")`, `SEARCH_INDEX_OBJECT_TYPE_RUMOR = "rumor"` in `SEARCH_INDEX_OBJECT_TYPES`, and `r` in `SHORT_REFERENCE_PATTERN` / `NUMBERED_NAME_PATTERN`. Remove `RUMORS_DIR_NAME`.
3. Replace `core/rumors.py` with `core/rumor.py` implementing create/get/list/update/promote/dismiss/reopen/archive/renumber with the guards above. Reuse the boss helpers (`_safe_path`, `frontmatter_utils.write_post`, summary validation, archive moves, `git_utils` attribution) rather than duplicating them. Add `templates/sourcebook/rumor.md` if creation follows the boss template pattern.
4. `core/references.py`: add the `rumor` domain (live and archive inventories; `rNNN` syntax in the `inputs` docstring). `core/search_index.py`, `index_snapshot.py` and `recovery.py`: index, snapshot and recover rumor records as managed objects, wherever those modules handle each type explicitly. Keep snapshot `VERSION = "1"`.
5. Replace `cli/rumors.py` with `cli/rumor.py` (register `rumor` in `cli/app.py`) and `mcp/rumors.py` with `mcp/rumor.py` (update `_TOOL_MODULES` in `mcp/server.py`). Both are thin wrappers using `references.inputs("rumor", ...)`, and every CLI print of stored content uses `markup=False`.
6. Update the owning docs per Requirement 10 and both skill flavors per Requirement 11. Then grep `templates/` for `rumors_`, `bosses/rumors` and `cac rumors`. Zero hits are expected outside `branching-guide.md` and `migration-guide.md`; record the hits that remain there for e024.
7. Tests mirroring the source:
   - Replace `tests/{core,cli,mcp}/test_rumors.py` with `test_rumor.py`.
   - Cover every lifecycle transition and refusal:
     - update when not open; update as a full replacement;
     - promote to an assigned, withdrawn or vanquished boss or a missing boss; promote with and without a message; several rumors promoted to one boss, with the boss file byte-identical before and after;
     - dismiss without a reason; reopen without a message; reopen when archived, and `history` entries preserved across reopen;
     - archive when open;
     - renumber of a promoted or archived rumor or to an existing name; renumber of an open and of a dismissed rumor succeeding; renumber after reopening a promoted rumor succeeding;
     - literal create versus short ref.
   - Cover `rNNN` resolution (live, archived, ambiguous), list status filtering, an invalid status, cursor paging, and `rumor_get` continuation of a long body.
   - Cover search indexing under type `rumor`, an index built before any rumor staying fresh through rumor creation, and recovery of a failed rumor write.
   - Update `tests/mcp/test_server.py::test_all_domain_tools_are_registered` to replace the five `rumors_*` names with exactly the nine `rumor_*` names.
   - Add a CLI test asserting `cac rumor -h` lists exactly the nine commands and `cac rumors` no longer exists.
   - Add one end-to-end CLI test in `tests/cli/test_rumor.py`, using the suite's existing temporary-project fixtures and `CliRunner`: create, list, get, update, renumber, promote to a created boss, refused renumber while promoted, dismiss, reopen, archive and index search, plus a bracketed `[tool.pdm]` value in `origin` that prints intact.
   - Update `test_skills.py` per Requirement 11, and fix the other tests that reference the old model (`test_boss.py`, `test_boss_candidates.py`, `test_campaign_bosses.py`, `test_index_snapshot.py`) at the cause.
8. Run `pdm run pytest -q`, `pdm run ruff check .` and `pdm run ruff format .`, and fix any failures at the cause.
9. Record the results (files changed, test counts, the grep results from step 6) with `encounter_record_message`.
10. Commit as "Promote rumors to standalone numbered records (e023)". Do not push. Ask the developer to redeploy skills with `cac bootstrap init` and to restart the MCP server so the new tools load.

## Verification

- `cac rumor -h` lists exactly the nine commands; `test_all_domain_tools_are_registered` asserts exactly the nine `rumor_*` tools; `cac rumors` and every `rumors_*` tool are gone.
- Files live at `.sourcebook/rumors/rNNN-slug.md` (archived under `archive/rumors/`), and nothing is written under `bosses/rumors/`.
- Promotion links only to unassigned proposed/available bosses, leaves the boss file unchanged, and allows many rumors per boss.
- Renumbering succeeds only for live open or dismissed rumors and is refused for promoted and archived ones.
- `history` records every promote, dismiss and reopen message and survives updates and reopens.
- The `rNNN` short ref resolves, including archived records, and rejects ambiguity.
- Rumors appear in `index_search` under type `rumor`; an existing index stays fresh; `prime_get` output is unchanged.
- `workflow.md`, `tool-reference.md` and both flavors of the skill templates describe only the new model. The step-6 grep finds no stale reference outside the two guides deferred to e024. `test_skills.py` passes with the `rumor` regex.
- Stored text containing brackets prints intact on the CLI.
- `pdm run pytest -q` passes; `ruff check .` reports zero errors; `ruff format .` changes nothing.
- After the developer redeploys, the deployed skill copies match their templates.
- The developer confirms completion.

## Log

### Review - 2026-10-28T14:54:20Z - John Hoff

Independent review: PASS-WITH-NOTES. clean-tests-and-lint honored: pytest, ruff check and ruff format are gated in step 8 and the Verification. cli-mcp-parity honored: nine CLI commands match nine MCP tools; the editor fallback becomes required MCP args; paginate/fit_response contracts, _TOOL_MODULES and test_all_domain_tools_are_registered are updated; the old rumors surface is removed on both sides. console-best-practices honored: markup=False for body, summary, origin, resolution and history, with a bracket round-trip test. skills-authored-only-in-templates honored: template-only edits in both flavors, the test_skills regex goes from rumors to rumor, and the developer redeploys. workflow-doc-source-of-truth is honored in intent, but before execution, extend Requirement 10 and the step-6 check. tool-reference.md lines 53, 121 ('Rumors do not participate in resolution'), 165, 172 ('cac rumors delete') and 473 ('excludes rumors', index coverage) sit outside the Rumors contract section and become false. workflow.md line 412 and prose skill references (world_planner line 79, campaign_manager lines 10 and 120) would escape the narrow grep for rumors_, bosses/rumors and cac rumors, so replace it with a case-insensitive 'rumor' grep over templates/ with each hit reviewed by hand. Unverified, outside the cited surface: index freshness with snapshot VERSION 1 after adding a type; whether identity_page and the reused boss helpers exist as named; -s/-o option collisions; stale rumors references elsewhere in src/. Process: commit the pending sourcebook changes before step 1's clean-tree check, and limit the 'never internally inconsistent' claim given the e024 deferral of branching-guide and migration-guide.

### Opened - 2026-10-28T14:58:51Z - John Hoff

Opened with developer approval after committing the draft and campaign revision (clean tree). Deviations adopted from the review notes: (1) step 6 uses a case-insensitive "rumor" grep over templates/, reviewing each hit by hand, and Requirement 10 explicitly includes tool-reference.md lines 53, 121, 165, 172 and 473 and workflow.md line 412, plus prose references in the skill templates; (2) the claim that the branch is never inconsistent is limited to code, owning docs and skills, since branching-guide.md and migration-guide.md stay stale until e024; (3) assumptions about index freshness at VERSION 1, helper names and importability, -s/-o collisions, and other src/ rumors references are checked first, and any that prove wrong are logged.

### Message - 2026-10-28T15:23:50Z - John Hoff

Plan steps 2-8 done. Code: config (RUMOR_DIR_NAME at the sourcebook root, RUMOR_STATUSES, rumor search type, r in short/numbered patterns, RUMORS_DIR_NAME removed); new core/rumor.py plus templates/sourcebook/rumor.md; references gains the rumor domain (rNNN), and the shared inputs adapter gains a renumber case so results carry the new name's identity; search_index/index_snapshot index and snapshot live and archived rumors (summary, origin and body searchable; VERSION stays "1"); boss.py and references.py drop the reserved "rumors" boss-namespace special case; cli/rumor.py and mcp/rumor.py replace the deleted rumors modules (registered in app.py and _TOOL_MODULES). Recovery needed no change: it is path-classified and generic. Assumption checks: identity_page and the boss helpers exist and are importable; -s/-o do not collide; no other src/ references to rumors remain; an existing index stays fresh (tested). Tests: new tests/{core,cli,mcp}/test_rumor.py (47 core, CLI end-to-end walkthrough, exact nine-command help, nine-tool registration with required MCP args, paging, continuation, recovery of a failed renumber, inconsistent-metadata rejection); updated test_boss, test_boss_candidates, test_campaign_bosses (rumor promoted to a campaign boss stays byte-identical through complete/reactivate/archive), test_index_snapshot, test_skills (regex now `rumor`), and test_server (exactly nine rumor_* tools). Docs and skills: workflow.md rewrites all rumor statements (domain table, connections, branch-settings purpose, boss storage note, campaign archive note, new Rumors section, ownership, numbering, planning handoff); tool-reference.md has a new Rumors contract section plus fixes to lines 53, 103 (rNNN), 121, 165, 172, the input matrix, search coverage and index coverage. Both flavors of world_planner and campaign_manager were rewritten identically apart from tool prefixes. world_manager mentions no discoveries, so no pointer was added. The case-insensitive grep over templates/ finds stale rumor text only in branching-guide.md (lines 24-38, 110-128) and migration-guide.md (lines 123-134), both deferred to e024. Deviations: (1) renumber refreshes updated_by/updated_on, documented in tool-reference; all other fields are unchanged. (2) Rumor bodies are frontmatter records like bosses, so line endings and trailing whitespace are normalized, where the old raw document round-tripped bytes exactly. (3) test_docs caps workflow.md at 40,000 characters; the first draft reached 40,661, so the Rumors section was condensed to procedure and lifecycle with field-level detail kept in tool-reference (now 39,593; the cap was not raised). Gate: pytest 1601 passed; ruff check clean; ruff format applied to 4 new or edited files, then left 288 unchanged.

### Completed - 2026-10-28T15:46:28Z - John Hoff

Verification passed. Code, docs and skills committed in 8281dca; pytest 1601 passed, ruff check and format clean. Developer ran cac bootstrap init and restarted the session. All six deployed skill copies match their templates (line-ending-normalized diff), and the restarted MCP server serves the rumor_* tools (rumor_list returns an empty page) with rumors_* gone. Developer confirmed completion.
