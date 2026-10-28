---
archived: false
campaign: c001-boss-edition
created_by: John Hoff
created_on: '2026-10-28T03:25:23Z'
depends_on:
- e018-exact-canonical-names-win-short-reference-resolution
kind: scripted
name: e019-restructure-workflow-guide-and-tool-reference
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-10-28T03:47:56Z'
---

## Requirements

Restructure the packaged Workflow Reference Guide (`packages/crypts-and-commits/src/cac/core/templates/docs/workflow.md`) so it is readable as the single source of truth again. Move field-level tool contracts into a new packaged tool reference, and stop skills from loading the whole guide during routine orientation. This is a documentation, skill-routing and lore change: no MCP/CLI behavior, signature, lifecycle or schema changes.

Background: the guide is about 63,550 of its 64,000-character `DOCS_RESPONSE_BUDGET`. Repeated budget pressure across e005–e018 compressed its prose into telegraphic fragments. It ships repo-specific history to every bootstrapped project (sample reports naming `c001/e010-expand-encounter-handoff-reporting` and `c001-boss-edition`, plus references to e005 and e014). The redeployed `campaign-manager` and `world-planner` skills, in both providers, also tell agents to read the whole guide while orienting, which costs about 16k tokens per session.

1. **workflow.md keeps procedure and the domain model.** It covers purpose, the domain model and cross-type connections, status lifecycles and guards, explicit user gates and the review flow, the planning/campaign/branch procedure, the priming and disclosure ladder, archiving, schema versioning, and developer-only maintenance (bootstrap, index rebuild, Codex patch guard). Use complete, plain sentences rather than compressed fragments, and generic placeholder examples (`c00N-example`) instead of this repository's campaign or encounter names. Keep a short worked lifecycle example.
2. **A new packaged doc holds the tool contracts.** Proposed name: `tool-reference`, registered in `core/docs.py` with a routing summary and loadable from built wheels. It holds the field-level contracts the guide carries today: per-domain operation tables (MCP tool and CLI equivalent), arguments, result and identity shapes, error and guard conditions, response budgets and cursor continuation, the short-reference grammar and operation/input matrix, candidate and rumors envelopes, prime/search result fields, and CLI body-file input. Each contract appears in one place. workflow.md links to it instead of repeating it.
3. **Codex handoff guidance shrinks to its requirements.** The guide keeps a concise statement of what Codex draft and review reports must cover. The long sample reports are removed, since the packaged Codex `campaign-manager` skill already carries the operative guidance; adjust that template only if a requirement would otherwise be lost.
4. **Nothing normative is lost.** Every rule in the current guide must end up in workflow.md or the tool reference, or be removed with a stated reason (duplicate, obsolete, or repo-specific history). Record the section-by-section mapping in an encounter message during execution.
5. **Both docs fit comfortably.** Each must be retrievable whole at the unchanged 64,000-character budget, with workflow.md targeted well below it (aim for 40,000 characters or less) so future changes have room. Do not raise any budget.
6. **Skills load procedure on demand.** In both providers' packaged templates (`core/templates/skills/{claude,codex}/`):
   - `campaign-manager` and `world-planner` orientation should stop instructing a full read of `workflow`. Point to the specific sections, or the tool reference, only when a procedural or contract question arises.
   - `world-manager`'s docs section lists the new reference.
   - The branching and migration guides update their cross-links.

   Keep both providers consistent. Deployed copies are untouched; redeployment is developer-only.
7. **The `workflow-doc-source-of-truth` lore is updated in this encounter** (developer-approved while drafting). Today it requires workflow.md itself to describe MCP tool names, arguments and return shapes, which conflicts with moving contracts to the reference. Update it through `lore_update` (CLI fallback `cac lore update`) so that:
   - workflow.md and `tool-reference.md` are a paired source of truth. workflow.md owns the domain model, status lifecycles and guards, cross-type connections, and workflow procedure (gates, review flow, disclosure ladder, planning/branch procedure). `tool-reference.md` owns MCP tool and CLI command names, arguments, result shapes, errors, budgets and continuation.
   - A substantive change must update whichever document owns the affected statement, in the same change. A change that touches both kinds updates both.
   - The review instruction checks the owning document instead of workflow.md alone. Missing updates remain lore violations.

   Keep its region assignment and enabled state, and update its routing summary in the same `lore_update` call. Make the update when the two documents exist, before verification, so the encounter's own changes are checked against the new rule. `cli-mcp-parity` does not name workflow.md and needs no change. `CLAUDE.md`/`AGENTS.md` mentions of this lore remain with the campaign's adoption encounter.
8. **Discovery text stays accurate.** Update `README.md`, `packages/crypts-and-commits/README.md` and `docs/QUICKSTART.md` where they describe docs retrieval, minimally. `CLAUDE.md`/`AGENTS.md` and `docs/boss-edition.md` drift remain with the campaign's adoption encounter.

## Rationale

The guide's job is to be the authoritative description of how CAC works, for developers and for agents with a procedural question. Budget-driven compression made it hard to read, and its tool-contract detail duplicates tool docstrings and CLI help while crowding out procedure. Separating procedure from contracts restores readability, gives both documents headroom, and lets skills fetch only what they need. Repo-specific examples should not ship to other projects.

Updating the source-of-truth lore in the same encounter avoids leaving the restructured layout in apparent violation of a rule that reviews enforce on every later encounter. The developer approved the lore change during drafting. Doing all of this before the adoption encounter means that encounter documents the final document layout.

## Plan

1. Prime through world-manager and confirm campaign state. Read the current `workflow.md` in full (through `docs_get("workflow")` pages or the source file, since it is a packaged template, not managed content), and also `branching-guide.md`, `migration-guide.md`, `core/docs.py`, `core/config.py` (`DOCS_RESPONSE_BUDGET`), and the six skill templates. Read `tests/core/test_docs.py`, `tests/core/test_boss_docs.py`, `tests/cli/test_docs.py`, `tests/mcp/test_docs.py`, `tests/core/test_templates.py` and `tests/core/test_skills.py`. Hydrate the current `workflow-doc-source-of-truth` lore with `lore_get`.
2. Build a section inventory of normative statements and classify each as procedure, contract, duplicate, obsolete, or repo-specific. Record the mapping in an encounter message before rewriting.
3. Write `tool-reference.md` from the contract statements, checking each against current code with CodeGraph (tool signatures in `mcp/`, CLI options in `cli/`, result shapes in `core/`), and fix any statement that is already inaccurate. Register it in `core/docs.py` and the package data, so `docs_list`/`docs_get` and `cac docs list/get` expose it with no new tool.
4. Rewrite `workflow.md` around procedure in plain prose with generic examples and links to the reference. Shrink the Codex handoff section as described in Requirement 3.
5. Update `workflow-doc-source-of-truth` with `lore_update` (body plus summary) as described in Requirement 7, and record the new text in an encounter message.
6. Update the skill templates for both providers, the guides' cross-links, and the minimal README/Quickstart discovery text.
7. Tests: update `test_boss_docs.py` heading and tool-name pins to check the document where each statement now lives. Add registry, summary, whole-retrieval-at-budget and built-wheel resource coverage for the new doc, following the existing guide tests. Add a test that workflow.md contains no `c001`/`e0NN` repository references. Keep the skill deployment tests passing. Assert behavior and placement, not prose.
8. Run focused docs/skill tests, then `pdm run pytest -q`, `pdm run ruff check .` and `pdm run ruff format .`. Report sizes, the mapping, the lore change, and the redeployment follow-up, and ask for developer confirmation before completing.

## Verification

- Every normative statement in the old guide maps to workflow.md, the tool reference, or a recorded removal reason; the mapping is in the encounter log.
- Spot-check about ten contracts in the tool reference against code (tool arguments, result fields, CLI options) and record the results.
- Both documents are retrievable whole at the unchanged 64,000-character budget, and workflow.md is at or below about 40,000 characters. `docs_list`/`docs_get` and `cac docs list/get` expose `tool-reference`, which loads from a built wheel.
- workflow.md contains no references to this repository's campaigns or encounters, and uses complete sentences rather than compressed fragments; a reviewer reads a sample of sections to confirm.
- `lore_get("workflow-doc-source-of-truth")` shows the paired-ownership rule and an updated summary, with its region assignment and enabled state unchanged. This encounter's own MCP/CLI/skill statements live in the document that rule assigns them to.
- Both providers' `campaign-manager` and `world-planner` templates no longer load the whole guide during orientation, and they route to sections or the reference consistently. Deployed copies are untouched.
- `pdm run pytest -q` passes, and `pdm run ruff check .` and `pdm run ruff format .` are clean, with no skips, suppressions or weakened tests. No MCP/CLI behavior changed.

## Log

### Review - 2026-10-28T03:28:37Z - John Hoff

Reviewed against world lore (clean-tests-and-lint) and crypts-and-commits region lore (cli-mcp-parity, console-best-practices, skills-authored-only-in-templates, workflow-doc-source-of-truth). Tests and lint are gated in Plan step 8 and Verification. There is no CLI/MCP surface change: tool-reference is exposed through the existing docs_get and cac docs get. Console rules do not apply. Skill edits are limited to both providers' packaged templates, deployed copies stay untouched, and redeployment is left to the developer. Under its current text, workflow-doc-source-of-truth would forbid moving tool contracts out of workflow.md. The encounter resolves this openly by amending that lore to a paired workflow.md/tool-reference.md ownership rule, developer-approved during drafting and applied before Verification, so this review accepts the amended rule as the standard for this encounter. Notes for execution: (1) make sure workflow.md's disclosure-ladder or orientation procedure describes the new on-demand skill routing, since that change is itself a skill-procedure change; (2) have the rewritten lore also name world-planner alongside world-manager and campaign-manager; (3) keep the examples behind the templates' 'Follow workflow's examples' lines, or update those lines, so they still point to something; (4) the CLAUDE.md, AGENTS.md and boss-edition.md drift deferred to the adoption encounter remains until that encounter lands; (5) the built-wheel test should confirm the package data includes the new doc.

### Opened - 2026-10-28T03:29:29Z - John Hoff

Developer approved opening after PASS-WITH-NOTES review; reviewer notes 1-5 will be addressed during execution.

### Message - 2026-10-28T03:31:27Z - John Hoff

Section mapping (Plan step 2), old workflow.md section -> destination. W = workflow.md, T = new tool-reference.md.
- Purpose -> W (adds the paired-ownership statement and link to T).
- CLI body input -> T (CLI body input).
- Domain model at a glance -> W.
- World: frontmatter and lore connection -> W; operation table -> T. Branch settings: default/absence/backfill/preservation semantics and "settings prove nothing about branches" -> W; setter command forms and example -> T. Schema versioning -> W.
- Lore, Region: frontmatter, body, status, connections -> W; operation tables -> T.
- Campaign: frontmatter, body locking, lifecycle table and diagram, connections -> W; operation table -> T. Archiving: status independence, guard, cascade, storage layout, no unarchive -> W; include_archived list/search flags and index_status counting -> T.
- Encounter: frontmatter, body sections, lifecycle table/diagram, record-message states, draft-only assignments, connections, kinds -> W; closed-campaign mutation refusal and read access -> W (guard); operation table and optional campaign argument/active fallback -> T.
- Explicit user gates -> W unchanged in substance, including the requirement that both campaign_manager templates carry each gate's stop-and-ask wording.
- Codex encounter handoffs -> W condensed to the required content of draft and review reports and verdict handling. Removed: the four illustrative sample reports (repo-specific: they name c001/e010-expand-encounter-handoff-reporting, c001-boss-edition and e005; the packaged Codex campaign-manager skill already carries the full operative report guidance, so no template change is needed).
- Agent planning and campaign workflow (skill ownership, orient/plan/allocate, selection/branches/collision checks, completion/reactivation, reconciliation and planning handoff) -> W, rewritten as prose; this is where the templates' "workflow's examples" now point (a named "Reconciliation examples" subsection). Inventory argument details -> T.
- Boss planning records: storage, frontmatter, body headings, lifecycle guards, standalone archive rules, dependency graph rules, schema/no-migration rules -> W (adds a boss status table derived from the same guards); operation table, body+summary input rule, list/get result shapes, rollback behaviour -> T. "Pre-e014 libraries" -> rephrased as "libraries that predate roadmap adoption" (repo-specific encounter number).
- Roadmap adoption: progress mapping, provenance semantics, completed_on rule, readiness/ownership rules, worked b001-b003 example -> W; boss_record signature and CLI flags -> T.
- Campaign rumors: storage and content semantics, owner rules, lifecycle independence, execution/planning roles -> W; operation table, CLI flags, delete confirmation, result envelopes, list items/diagnostics -> T.
- Candidate discovery: pool and classification semantics, link consistency rules, order is not priority -> W; page/count/item fields, reason and diagnostic codes, roadmap fields, budget limits -> T.
- Promotion and campaign coupling: membership semantics, selection rules, set-bosses rules, retry semantics, lifecycle effects on bosses, archive effects, deletion protection -> W; signatures and boss_assign_campaign output fields, preflight/rollback/RecoveryError -> T. The duplicated archive-inventory paragraph at the end of that section -> T, merged with the Archiving list rule (duplicate).
- Numbered references and canonical identity, Operation/input matrix, Identity and budgets -> T (W keeps a short statement that numbering is a skill convention and core allocates nothing).
- Cross-cutting priming/search/docs: prime and search concepts and the disclosure ladder (now including on-demand doc routing) -> W; prime result fields and truncation shape, search freshness/stale contract and result shapes -> T; developer-only index rebuild -> W. Removed: "Demo's read-only core adapter reports unavailable/stale/no hits" (repo-specific to this repository's demo-api package). Docs routing -> W (which doc to read when) and T (docs_list/docs_get).
- Example lifecycle -> W, generic.
- Bootstrap and Codex patch guard -> W (developer-only maintenance).

### Message - 2026-10-28T03:36:11Z - John Hoff

Lore updated (Plan step 5): workflow-doc-source-of-truth now defines workflow.md and tool-reference.md as a paired source of truth. workflow.md owns the domain model, lifecycles and guards, cross-type connections, and world-manager/world-planner/campaign-manager procedure (gates, review flow, disclosure ladder, planning/branch procedure); tool-reference.md owns MCP/CLI names, arguments, result and identity shapes, surfaced errors, budgets and continuation. A substantive change updates whichever document owns the affected statement, both when both kinds change; the review instruction checks the owning document(s) and covers any skill's SKILL.md template. Summary regenerated in the same lore_update; region assignment and enabled flag untouched (reviewer note 2 addressed: world-planner is named).

Docs written: workflow.md 39.1k chars, tool-reference.md 29.0k chars (budget 64,000 unchanged). Corrections found while checking contracts against code: campaign deletion is guarded only by the bosses list (current or historical) and reverse boss claims, not by archived state (the skill templates' "archived state" claim is inaccurate; logged as a rumor rather than changed here, since the templates' deletion paragraph is out of this encounter's scope). The old guide never listed CLI --yes on lore/region/campaign/encounter delete or cac prime applicable-lore --cursor; the tool reference now does. Deviation from Plan step 7: no existing test builds a wheel (pdm-backend is not installed in the workspace venv), so built-wheel inclusion is checked during verification with `pdm build` and a wheel listing, and test coverage follows the existing importlib.resources guide tests.

### Message - 2026-10-28T03:45:59Z - John Hoff

Verification results.
- Mapping: recorded in the 03:31 message; every old section maps to workflow.md or tool-reference.md, with removals stated (Codex sample reports, demo-api adapter line, duplicate archive-inventory paragraph; e005/e014/c001 references dropped or rephrased).
- Contract spot-checks against code (all match the reference): (1) every MCP tool signature and (2) every CLI command/option, via a dump of server.mcp.list_tools() and the Typer command tree, from which the operation tables were written; (3) prime truncations {field, notice:"TRUNCATED", ref:{tool,name?}} and the "metadata cannot fit" failure (core/prime.py present); (4) index_search built/stale/hits/diagnostic and StaleIndexError diagnostic code/message/recovery (mcp/index.py, core/search_index.py); (5) index_status built/counts/freshness/diagnostic; (6) boss_candidates envelope items/next_cursor/counts/healthy/diagnostics/diagnostics_omitted/diagnostics_ref and the quarter-budget diagnostic cap (core/boss_candidates.py); (7) the 16-entry detail limit and prerequisites_omitted/diagnostics_omitted/summary_truncated on items; (8) boss_assign_campaign boss/campaign/status/reused/boss_identity/campaign_identity plus identity (core/coupling.py, core/references.py); (9) identity canonical/short/reason/campaign/bare_short and campaign_-prefixed parent reasons, and identity_page items/identities/next_cursor (core/references.py); (10) rumors get truncated/next_cursor/notice, mutation campaign/identity, list campaign/identity/diagnostic (core/rumors.py); (11) campaign delete guard = bosses list or reverse claims only (core/coupling.py), which corrected the skills' "archived state" claim; that discrepancy is logged in the campaign rumors.
- Sizes: workflow.md 39,121 chars (target <=40,000), tool-reference.md 29,032 chars; budget unchanged at 64,000. Both are retrieved whole by docs_get and cac docs get (tests); a test pins workflow.md at <=40,000.
- Exposure: in-process docs_list/docs_get and cac docs list/get return tool-reference (tests and manual CLI run). The already-running MCP server in this session still lists the old three docs because it was started before the change; it will pick up tool-reference after a restart (no code change involved). Built wheel: `pdm build` produced crypts_and_commits-0.2.0-py3-none-any.whl containing cac/core/templates/docs/tool-reference.md, and `python -I` against the extracted wheel loads both docs within budget with all four registered (reviewer note 5).
- No repository references: test asserts no cNNN/eNNN-with-leading-zero IDs or "boss-edition" in workflow.md or tool-reference.md; confirmed the same pattern finds c001/e010/e005/e014/boss-edition in the old guide. Prose sampled: Purpose, Bosses, Agent planning and campaign workflow, and Codex handoffs are in complete sentences.
- Lore: workflow-doc-source-of-truth shows the paired-ownership rule and new summary; assignment to the crypts-and-commits region and enabled=true unchanged. This encounter's statements are placed accordingly (contracts in the reference, procedure in the guide; reviewer note 1: the disclosure ladder in workflow.md now describes on-demand routing and that campaign-manager/world-planner skip the docs during orientation).
- Skills: both providers' campaign-manager and world-planner templates no longer instruct a workflow read during orientation and route to named sections or tool-reference on demand; "Follow workflow's examples" now points to the named "Reconciliation examples" subsection (reviewer note 3); world-manager lists tool-reference in its Docs section and ladder step 4. All three explicit user gates in both campaign_manager templates are untouched. Deployed .claude/.agents copies untouched (git diff empty).
- Discovery text: README.md, packages/crypts-and-commits/README.md and docs/QUICKSTART.md updated minimally; branching and migration guides cross-link tool-reference.
- Checks: `pdm run pytest -q` 1564 passed; `pdm run ruff check .` clean; `pdm run ruff format .` 284 files unchanged. No MCP/CLI behavior changed (only docs.py registry entries and summaries).
- Follow-ups for the developer: run `cac bootstrap init` to redeploy the updated skills; restart the MCP server; CLAUDE.md/AGENTS.md/docs/boss-edition.md drift stays with the adoption encounter (reviewer note 4).

### Completed - 2026-10-28T03:47:56Z - John Hoff

Developer confirmed completion after verification: workflow.md 39,121 chars, tool-reference.md registered and wheel-packaged, lore updated, skills route docs on demand, 1564 tests passed, ruff clean.
