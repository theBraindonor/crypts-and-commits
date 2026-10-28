---
archived: false
campaign: c001-boss-edition
created_by: John Hoff
created_on: '2026-10-28T02:27:32Z'
depends_on:
- e011-add-campaign-rumors
- e013-support-multiple-bosses-per-campaign
- e016-add-branching-and-migration-guides
kind: scripted
name: e017-fix-review-findings-and-supported-continuation-reads
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-10-28T02:56:47Z'
---

## Requirements

Fix the confirmed correctness findings from the post-e016 campaign review, and remove the last place where CAC tells an agent to read managed files directly.

1. **Scoped ownership validation.** `coupling.campaign_operation` (which wraps every campaign lifecycle operation, including update/open/pause/complete/abandon/reactivate/archive/delete) and `coupling.preflight_campaign_creation` currently build `Links(root)`, which fully loads and validates every boss and campaign record. One malformed or legacy record anywhere therefore blocks operations on unrelated campaigns. Change this so that an operation validates only the records that bear on the target campaign:
   - the target campaign itself;
   - every boss in its `bosses` membership;
   - every boss whose `campaign` field claims it;
   - for an abandoned campaign, the other campaigns that now own its released origins (the existing `_pair` check).

   Finding claims still means reading each boss's frontmatter `campaign` field. A boss whose frontmatter parses, and whose `campaign` field is absent or names another campaign, is unrelated; its other defects (name/status/archive mismatch, provenance) must not block the operation. A boss file whose frontmatter cannot be parsed at all could hide a claim, so it still fails closed with an actionable error naming that file's canonical boss. Defects in related records keep failing exactly as today. Campaign creation applies the same claim scan. Ownership semantics, reciprocity rules, deletion protection and Recovery cohorts are unchanged; this only narrows which unrelated records can block an operation.

2. **Legacy campaign status on assignment retry.** `coupling.assign_campaign` reads `links.campaigns[campaign_name][1]["status"]` on the idempotent-retry path, while `_campaign` and `Links.current` treat a missing status as `draft`. A legacy campaign file with no `status` key raises an uncaught `KeyError`, which surfaces as a CLI traceback or an MCP internal error. Use the same `draft` default, and check the other coupling/campaign_bosses/prime call sites for the same pattern.

3. **Get responses honor their budget.** Fallback truncation in the shared reference adapter (`references.inputs`, plus `references.body_allowance` for the CLI path) reserves room only for identity metadata. It also measures raw characters rather than serialized JSON, so `encounter_get` and non-provenance `boss_get` results can exceed `RESPONSE_BUDGET`. `campaign.budget_response` and `boss.budget_response` already fit the whole serialized envelope, but they are near-duplicates. Replace them with one shared core helper in `core/budget.py` that fits any get envelope (metadata, summary, identity and escaping included). Use it for every domain get that truncates a body: world, lore, region, campaign, boss and encounter.

4. **Supported continuation instead of direct file reads.** `budget.truncate_body`'s notice tells the caller to "read the full content directly from disk" at a `.sourcebook/` path, which contradicts the MCP/CLI-only guardrail. Encounter bodies in this campaign routinely exceed the budget (e008, e009, e014 and e015), so this guidance is followed in practice. e011 solved the same problem for rumors with content-bound continuation cursors. Generalize that mechanism into shared core and adopt it for the six domain gets:
   - Add an optional `cursor` argument to `world_get`, `lore_get`, `region_get`, `campaign_get`, `boss_get` and `encounter_get`, and a matching `--cursor` option to the CLI gets.
   - A truncated response carries a notice naming the continuation call (not a file path) and a `next_cursor`.
   - Continuation pages return further body text under the same serialized budget, and the pages reassemble the exact body with no gaps or duplicates.
   - A cursor is bound to the body's content hash, so it fails clearly after the record changes. Invalid cursors also fail clearly.
   - Responses that fit, and responses without a cursor, keep their current fields and shape apart from the additive `next_cursor` and the changed notice text.
   - Prime's truncation hydration refs keep pointing at the domain gets, which can now be continued.

   Rumors keep their existing contract; if both can share one implementation without changing rumors' outputs, do that.

5. **Docs and skills.** Update tool docstrings, CLI help, the packaged Workflow Reference Guide, and both providers' packaged skill templates wherever they tell agents to read a reported path when output is truncated, so they describe the continuation call instead. The guide is at 63,675 of its 64,000-character `DOCS_RESPONSE_BUDGET`: consolidate prose to fit and do not raise the budget. Skill changes go only in `core/templates/skills/{claude,codex}/`; redeployment stays developer-only.

Out of scope, and kept for later work:
- the short-ref shadowing of literal short-shaped legacy names (pending a developer decision);
- search freshness hashing cost, repeated candidate evaluation, and the duplicate inspection in `cac campaign get`;
- test-module layout;
- `CLAUDE.md`/`AGENTS.md`, world summary, campaign body and `docs/boss-edition.md` drift (the item-13 adoption encounter);
- the low-confidence notes on mixed line endings, `MembershipError` and Log-section freezing.

## Rationale

A high-depth code review of `main...HEAD`, followed by spot checks against the source, confirmed these defects. Item 1 contradicts the campaign's own compatibility goal: one damaged or legacy record should be diagnosed, not make every campaign immutable. Item 2 is a crash on a documented legacy path. Item 3 means some get responses break the budget contract that the rest of the API enforces. Item 4 is a guardrail inconsistency: the framework's own tool output instructs agents to do what `CLAUDE.md` forbids, and this campaign's long encounter bodies trigger it regularly.

Fixing these before the adoption encounter means the guidance that encounter publishes describes behavior that holds. Generalizing e011's continuation and consolidating the two budget helpers removes duplication rather than adding a third copy.

## Plan

1. Prime through world-manager and confirm campaign state through campaign-manager. Use CodeGraph before reading or editing code. Main surface under `packages/crypts-and-commits/src/cac/`:
   - `core/`: `coupling.py`, `campaign.py`, `campaign_bosses.py`, `boss.py`, `references.py`, `budget.py`, `rumors.py`, `encounter.py`, `world.py`, `lore.py`, `region.py`, `prime.py`, `config.py`;
   - matching `cli/` and `mcp/` modules for world, lore, region, campaign, boss, encounter and rumors;
   - `core/templates/docs/workflow.md`;
   - `core/templates/skills/{claude,codex}/{world_manager,world_planner,campaign_manager}/SKILL.md`;
   - mirrored tests under `packages/crypts-and-commits/tests/`.
2. **Item 1.** Refactor `Links` (or add a scoped constructor) so campaign operations and creation load only the related records, with the claim scan described in Requirements. Keep `Links(root)`'s whole-store behavior where callers genuinely need it, such as candidate diagnostics, and check every existing caller. Add a regression test showing that a malformed unrelated boss and an inconsistent unrelated campaign no longer block update/open/pause/complete/abandon/archive/delete/create on a bossless campaign or on a healthy linked one. Add one showing that an unparseable boss still fails closed, and one showing that defects in related records still fail as before.
3. **Item 2.** Replace the subscript with the `draft` default. Find any other required-key reads of optional campaign fields. Add a retry test using a legacy campaign with no `status` key, through core, CLI and MCP.
4. **Item 3.** Add the shared envelope-fitting helper to `core/budget.py`. Move `campaign.budget_response` and `boss.budget_response` onto it, and route encounter/world/lore/region gets through it in core, so CLI and MCP share the result. Test serialized length against `RESPONSE_BUDGET` under patched small budgets, with large metadata, many regions/dependencies, and JSON-escaping-heavy bodies.
5. **Item 4.** Extract e011's hash-bound cursor logic into shared core, keeping rumors' observable contract. Add `cursor` to the six domain gets in core, MCP and CLI together. Change the truncation notice so it never names a filesystem path. Test full reconstruction of oversized Unicode and escaping-heavy bodies through CLI and MCP, stale cursors after an edit, invalid cursors, unchanged small responses, archived records, short-ref targets with cursors, and the MCP server's tool registration. CLI prints stored text with `markup=False`.
6. **Item 5.** Update docstrings, help, `workflow.md` (consolidating to stay within the budget), and both providers' skill templates. Search the packaged templates and docs for "read the file directly", "from disk" and similar wording, so none remains.
7. Run focused tests, then `pdm run pytest -q`, `pdm run ruff check .` and `pdm run ruff format .`. Record decisions and any deviation from this plan through `encounter_record_message`. Do not edit deployed skills, run bootstrap, or rebuild the real index. Ask for developer confirmation before completing.

## Verification

- **Item 1:** the unrelated-defect, fail-closed and related-defect matrix above passes for every wrapped campaign operation and for creation. Existing coupling, campaign_bosses, recovery and index-snapshot tests pass unchanged; any test changed must be explained in an encounter message rather than weakened.
- **Item 2:** a legacy no-status retry returns `reused=True` with status `draft` through all three surfaces, with no traceback.
- **Item 3:** every domain get's serialized MCP payload is at most `RESPONSE_BUDGET` under patched budgets and oversized inputs. An impossible minimum envelope still fails explicitly. Only one envelope-fitting implementation remains.
- **Item 4:**
  - Continuation reassembles exact bodies for all six domains through core, CLI and MCP, and stale or invalid cursors fail clearly.
  - No get output, docstring, help text, packaged doc or skill template directs an agent to read a `.sourcebook/` path; check this with a grep over `src/cac/` and the templates.
  - Rumors tests pass unchanged.
- **Item 5:** `workflow.md` is fully retrievable at the unchanged 64,000-character budget. Both providers' skills describe the same continuation route. Deployed `.claude/skills` and `.agents/skills` are untouched.
- `pdm run pytest -q` passes, and `pdm run ruff check .` and `pdm run ruff format .` are clean, with no skips, suppressions or weakened tests. Report results and the developer redeployment follow-up before asking to complete.

## Log

### Review - 2026-10-28T02:29:02Z - John Hoff

Reviewed against clean-tests-and-lint, cli-mcp-parity, console-best-practices, skills-authored-only-in-templates and workflow-doc-source-of-truth; the plan is consistent with all five. The new cursor is added to core, MCP and CLI together, with registration and both-surface reconstruction tests. CLI continuation output uses markup=False. Skill changes are template-only, and redeployment is left to the developer. workflow.md is updated in the same change with a fixed-budget retrievability check. The full pytest and ruff gate is required with no skips or weakened tests. Notes: (1) workflow.md has only about 325 characters of headroom, so the consolidation work is the main risk to watch; (2) cli-mcp-parity's text still names budget_core.truncate_body as the get-truncation contract, so consider updating that lore once the shared envelope helper lands; (3) the no-.sourcebook/-path grep may surface similar notices outside the six domain gets (docs_get, prime, index search, list tools), so decide up front whether such hits are fixed here or deferred, and record the decision as an encounter message; (4) the set of Links(root) callers that keep whole-store validation is not enumerated, so record it during implementation.

### Opened - 2026-10-28T02:30:30Z - John Hoff

Developer approved execution following independent PASS-WITH-NOTES review.

### Message - 2026-10-28T02:30:32Z - John Hoff

Scope decision for review note 3, approved by the developer: if the no-.sourcebook/-path check finds notices outside the six domain gets, any notice produced by the shared budget.truncate_body helper is fixed in this encounter, since the fix is mechanical. A notice with its own separate code path is recorded here and deferred.

### Message - 2026-10-28T02:55:05Z - John Hoff

Implementation and verification finished; awaiting developer confirmation.

Item 1: Links now takes an optional scope (campaigns=[...], bosses=[...]) and validates only the connected ownership component around it. That component is found by a fixpoint over raw boss `campaign` fields and raw campaign `boss`/`bosses` entries. Unparseable boss or campaign frontmatter still fails closed, naming the record. Scoped callers (review note 4): campaign_operation, preflight_campaign_creation, inspection, assign_campaign, create_group, set_bosses, and prime._active_bosses. No caller still needs whole-store validation; Links(root) with no scope keeps that behavior. Candidate discovery uses its own whole-store evaluator and is unchanged.

Item 2: the assignment retry now reads campaign status with the draft default. The same check found boss_candidates treating a missing campaign status as an invalid record; it now defaults to draft, consistent with coupling.

Items 3 and 4: core/budget.py has body_page (content-hash cursors, serialized measurement, optional custom measure) and fit_response. campaign.budget_response and boss.budget_response are deleted. truncate_body is also deleted, since it was the only source of path-naming notices. Each domain module has get_payload, shared by CLI and MCP. The reference adapter fits every result with a body. references.get_response gives the CLI the same identity-plus-fit result. world/lore/region/campaign/boss/encounter get, and docs_get under the scope decision, accept cursor (MCP) and --cursor (CLI). Rumors uses body_page with unchanged outputs. A truncated result adds next_cursor and a separate notice; complete results keep their exact shape. Docs keep body-character measurement, so full guides still fit 64,000.

Tests changed: truncation tests in cli test_lore, test_region, test_world, test_encounter, test_campaign, test_boss and test_docs asserted the removed .sourcebook/package path, or used budgets smaller than the metadata that whole-response fitting now counts. They now assert notice and next_cursor, the absence of any path, and realistic budgets. The MCP test_boss, test_campaign, test_references and test_docs assertions moved from body to notice. test_boss_record moved to fit_response. The six truncate_body unit tests were replaced with fit_response equivalents.

New tests: scoped-validation matrix, fail-closed unparseable boss, related-claimant still blocks, legacy no-status retry (core, CLI, MCP), body_page reassembly and cursor errors, cursor registration on seven get tools, six-domain CLI/MCP continuation parity with stale and invalid cursors, and archived records by short ref. All seven unrelated-defect and status tests failed on the pre-fix source.

Item 5: workflow.md documents shared continuation and is now 63,567 characters (it was 63,675). Both world-manager templates got one matching continuation paragraph and an explicit lore_get wording fix.

Checks: pdm run pytest -q passed 1545 tests. Ruff check and format are clean. git diff --check is clean. No get output, docstring, help, doc or skill tells an agent to read a reported path; the only remaining "from disk" text is index-rebuild docstrings. Deployed skills, hooks and bootstrap were untouched.

Follow-up: the developer redeploys templates and restarts the MCP server. Updating the cli-mcp-parity lore text (it still names truncate_body) is pending developer approval.

### Completed - 2026-10-28T02:56:47Z - John Hoff

Developer confirmed completion after verification: 1545 tests passed, Ruff clean, git diff --check clean, and no path-naming truncation guidance remains. Scoped ownership validation, the legacy status retry fix, whole-response budget fitting, and shared cursor continuation for all domain gets and docs_get are implemented. The cli-mcp-parity lore text is updated alongside. Follow-up: the developer restarts the MCP server and redeploys templates with cac bootstrap init.
