---
archived: false
campaign: c001-boss-edition
created_by: John Hoff
created_on: '2026-10-28T03:51:53Z'
depends_on:
- e019-restructure-workflow-guide-and-tool-reference
kind: scripted
name: e020-adopt-boss-edition-workflow-in-this-repo
regions:
- crypts-and-commits
status: open
updated_by: John Hoff
updated_on: '2026-10-28T04:06:30Z'
---

## Requirements

Campaign item 13: adopt the Boss Edition workflow in this repository's own instructions and sourcebook, following the packaged migration guide's "Update local instructions deliberately" stage and its "Targeted instruction mapping" (`docs_get("migration-guide")`). Also retire the campaign's design doc and rumors document, and record the release in the changelog. This is the final planned encounter of c001; afterward the campaign should be ready for its completion postmortem and implementation PR into `main`.

1. **Commit the developer's skill redeployment.** The working tree holds developer-run `cac bootstrap init` output that syncs `.claude/skills/{campaign-manager,world-manager,world-planner}/SKILL.md` and the matching `.agents/skills/` copies with the e019 templates. The agent does not edit these files; it only verifies that each deployed copy matches its `packages/crypts-and-commits/src/cac/core/templates/skills/{claude,codex}/<name>/SKILL.md` source byte-for-byte, then commits them.
2. **`CLAUDE.md` (shared guidance, imported by `AGENTS.md`).** Make targeted edits that replace obsolete CAC clauses, keeping unrelated policy and structure:
   - Project-purpose orientation paragraph: route static context to `world-manager`, goal/roadmap/readiness and rumor planning to `world-planner`, and tactical selection/execution to `campaign-manager`. Point to the Branching Guide and the workflow guide through docs retrieval rather than duplicating them.
   - Codex hook paragraph: the hook now denies only `apply_patch` targets inside managed sourcebook paths and does not filter shell calls. MCP/CLI-only access stays binding.
   - Architecture: `templates/docs/` now holds `workflow.md`, `tool-reference.md`, `branching-guide.md` and `migration-guide.md`; skill templates include `world_planner`; list the new `core`/`mcp` modules introduced in this campaign (boss, coupling, rumors, short refs, docs, index, etc., confirmed against the actual source tree) at the same level of detail as the existing entries.
   - Domain model: add bosses (statuses, `archived`, `depends_on`), campaign `bosses` membership and the `paused` status plus reactivation, rumors (one document per campaign), numbered names / short refs (`bNNN`, `cNNN`, `cNNN/eNNN`), and the world `merge_target_branch`/`planning_branch` settings. Fix the encounter lifecycle description where it has drifted (e.g. `kind`).
   - Agent skills section: three skills, not two, with one-line ownership for each.
   - A short branch-workflow note: the recommended planning / assignment / execution branches, with the procedure itself left to `branching-guide`/`workflow`.
3. **`AGENTS.md`.** Keep the import directive and the genuine Codex overrides. Add `world-planner` to the listed `.agents/skills/` skills and drop any wording that would conflict with the updated `CLAUDE.md`.
4. **Sourcebook (MCP only).** Refresh the world body (`world_set_body`): the domain model (bosses, rumors, numbered names), the full encounter lifecycle (`draft` → `reviewed` → `open` → `completed`, `abandoned`), the MCP-first/CLI-fallback guardrail and the branch workflow. Audit the summaries of `crypts-and-commits` region lore (`cli-mcp-parity`, `skills-authored-only-in-templates`, `workflow-doc-source-of-truth`, `console-best-practices`) and the `crypts-and-commits` region summary for obsolete two-skill, single-doc or pre-boss clauses, and update only what is actually stale (via `lore_update`/`lore_set_summary`/`region_set_summary`).
5. **Retire `docs/boss-edition.md`.** That file is the c001 design spec (942 lines). Its rules now live in the packaged `workflow`, `tool-reference`, `branching-guide` and `migration-guide` docs, and no tracked file outside the sourcebook links to it. Before deleting it, compare each of its sections (in particular "Decisions established so far", "Implementation decision record (e001)" and "Remaining implementation details") against the packaged guides. Any agreed decision or still-open item that appears in none of them is recorded, with its section reference, in the carry-forward encounter message described in Requirement 7, rather than being dropped. Then `git rm docs/boss-edition.md`. The campaign and encounter records that cite the path stay unchanged as history, and git history keeps the file.
6. **Add a Boss Edition entry to `docs/CHANGELOG.md`.** Follow the existing Keep-a-Changelog style. Use an `## [Unreleased] - Boss Edition` heading, because the migration guide states that the release number and tag have not been selected; do not invent a version or date. Give `Added` / `Changed` bullets at the same granularity as 0.2.0:
   - Added: bosses and their lifecycle/dependencies/candidates; recording an existing roadmap and historical completions; campaign boss membership (zero, one or many) with coupled lifecycle and `campaign_reactivate`/pause; rumors; numbered names and short refs; world branch settings; boss search and prime integration; continuation reads (`cursor`/`next_cursor`); the `world-planner` skill; the `tool-reference`, `branching-guide` and updated `migration-guide` docs.
   - Changed: CLI `--body-file` support; the narrower `apply_patch`-only Codex hook; campaign-manager/world-manager skill updates; the split of the workflow guide into procedure and tool reference.
   - Every bullet must match an actually completed c001 encounter or the shipped code. Check each one against the encounter list, and leave out anything that didn't ship.
7. **Delete the c001 rumors document (developer request).** Before deleting, record one carry-forward `encounter_record_message` on this encounter. It contains the full current rumors text verbatim, which today is two items: the campaign-deletion guard is misdescribed in the campaign-manager skills, and a long-running MCP server needs a restart to see new docs. It also contains any gaps from the Requirement 5 audit. Encounter Logs are durable history, so the follow-ups stay recoverable without being resolved or expanded here. Then call `rumors_delete(campaign="c001-boss-edition")`, and confirm with `rumors_get` that it now reports the document does not exist. No new rumors are created for c001 after this point.
8. **Verify adoption state** with supported reads only, per the migration guide's "Preserve in-flight work and verify adoption": all four registered docs readable without truncation, deployed skill owners consistent with local instructions, and world settings and campaign/encounter state inspected. Also disclose any branch-workflow gaps (e.g. the configured `planning` branch does not exist locally or on `origin`). Do not create or switch branches.

Out of scope: any `cac` source, template or packaged-doc change (gaps and existing rumors are carried in the encounter message, not fixed); `docs/QUICKSTART.md` changes; choosing a release number, bumping the package version or tagging; creating the `planning` branch; recording bosses; completing/pushing/merging the campaign; running bootstrap or index rebuild.

## Rationale

The campaign's own completion criterion requires the skills and docs to be consistent with each other. This repo dogfoods CAC, so its own `CLAUDE.md`, `AGENTS.md` and world body are the first adopter-facing instructions an agent reads, and they still describe the pre-Boss-Edition model: two skills, a three-object workflow, a Codex hook that filters shell, and only `workflow.md` in the docs. Leaving them stale would make every future session orient from wrong guidance and contradict the deployed `world-planner`/`campaign-manager` skills. The migration guide prescribes targeted edits over template replacement and reserves bootstrap for the developer. That is why this encounter only commits the developer's redeployment and edits user-owned instruction files and sourcebook content through supported interfaces.

The developer asked to remove `docs/boss-edition.md` before the PR into `main`. It was the campaign's working contract and has been superseded by the packaged guides. Leaving a 942-line pre-implementation design doc beside them would give adopters a second, partly outdated source of truth. The developer also asked to delete the c001 rumors document. Rumors deletion is deliberate, never automatic, so copying its contents and the audit gaps verbatim into this encounter's Log first means neither deletion loses an agreed decision or a known follow-up. The changelog entry gives the implementation PR and the eventual release a user-facing summary. It is marked Unreleased because no release number has been chosen.

## Plan

1. Re-check git status/branch (`c001-boss-edition`, not detached). Diff each deployed skill against its template source and confirm they are identical. Commit them as "Sync bootstrapped skills after e019 redeployment".
2. Inventory the actual `src/cac/core`, `cli` and `mcp` modules and `templates/` subpackages so `CLAUDE.md` and the changelog name only things that exist.
3. Edit `CLAUDE.md` section by section per Requirement 2, preserving the guardrail section's settings.json/permission semantics, tooling commands and repository layout verbatim except where they are obsolete.
4. Edit `AGENTS.md` per Requirement 3.
5. Read the world body and each listed lore/region via MCP. Update the world body and only the stale summaries/bodies per Requirement 4. Record which items were reviewed and left unchanged in an encounter message.
6. Audit `docs/boss-edition.md` against the four packaged guides per Requirement 5 and note any gaps. Re-grep tracked files (excluding the sourcebook) for `boss-edition.md`, then `git rm docs/boss-edition.md`.
7. Add the `[Unreleased] - Boss Edition` changelog entry per Requirement 6, cross-checking each bullet against the `encounter_list` of completed c001 encounters.
8. Read the full c001 rumors document (following any `next_cursor`). Record the carry-forward message per Requirement 7, holding the verbatim rumors plus the step-6 audit result (the gaps, or "none"). Then run `rumors_delete` and confirm the deletion with `rumors_get`.
9. Run the adoption verification reads per Requirement 8 and record the findings (including the missing `planning` branch) with `encounter_record_message`.
10. Run `pdm run pytest -q`, `pdm run ruff check .` and `pdm run ruff format --check .` (no source changes are expected, but the world gate applies).
11. Commit the instruction, changelog and doc-removal changes as "Adopt Boss Edition workflow in repo instructions (e020)". Do not push.

## Verification

- Each deployed `.claude/skills/*/SKILL.md` and `.agents/skills/*/SKILL.md` is byte-identical to its template, and both commits exist on `c001-boss-edition` with a clean working tree afterward.
- `CLAUDE.md` mentions `world-planner`, bosses, rumors, short refs, the branch settings and all four packaged docs. It no longer says the Codex hook blocks shell references, and it does not describe only two skills. Every module/template path it names exists.
- `AGENTS.md` lists all three Codex skills and still imports `CLAUDE.md`.
- `world_get` shows the refreshed body. Every reviewed lore/region item is either updated or explicitly recorded as unchanged.
- `docs/boss-edition.md` no longer exists, and no tracked file outside the sourcebook references it.
- `docs/CHANGELOG.md` has an `[Unreleased] - Boss Edition` section above `[0.2.0]` with no invented version or date, and every bullet maps to a completed c001 encounter.
- This encounter's Log holds the carry-forward message with both prior rumor items verbatim and the design-doc audit result. `rumors_get(campaign="c001-boss-edition")` reports that the document does not exist, and `rumors_list` no longer lists c001.
- `docs_get` for `workflow`, `tool-reference`, `branching-guide` and `migration-guide` returns untruncated bodies.
- `pdm run pytest -q` passes. `ruff check .` reports zero errors and `ruff format --check .` reports no diffs.
- The developer reviews the instruction, changelog and deletion diffs and confirms completion.

## Log

### Review - 2026-10-28T03:58:47Z - John Hoff

Independent review: PASS-WITH-NOTES. No Plan step conflicts with applicable lore. Deployed skills are only verified and committed, never edited (skills-authored-only-in-templates); no mcp/cli/core/template changes, so no owning-doc update is needed (workflow-doc-source-of-truth); console-best-practices does not apply. Notes to address in execution: (1) cli-mcp-parity names both `bootstrap` and `index rebuild` as CLI-only, but CLAUDE.md's guardrail paragraph and mcp/ architecture entry say only `bootstrap`; correct both and verify it. (2) Requirement 4 audits only lore/region summaries while Plan step 5 says summaries/bodies; the skills-authored-only-in-templates body still names only `{world_manager,campaign_manager}` and the region body lists only the original five core modules, so include bodies or record them as deliberately unchanged. (3) Update CLAUDE.md's skill-change sentence to name the workflow.md/tool-reference.md pair. (4) Apply `ruff format .` fixes rather than only `--check`. (5) Say how sourcebook changes are committed, or drop the clean-working-tree Verification claim. Flagged but unverified: possible stale wording in out-of-scope QUICKSTART/README files.

### Opened - 2026-10-28T03:59:22Z - John Hoff

Opened with developer approval. Execution deviations adopted from the review notes: (1) CLAUDE.md names both `bootstrap` and `index rebuild` as CLI-only (guardrail paragraph and mcp/ entry). (2) The Requirement 4 audit covers lore and region bodies as well as summaries; stale bodies are updated or recorded as unchanged. (3) CLAUDE.md's skill-procedure sentence names the workflow.md/tool-reference.md pair. (4) Step 10 runs `ruff format .` and applies any fixes. (5) The sourcebook state written through MCP (e020 record, world/lore/region updates, rumors deletion) is committed in the e020 commit, so the clean-working-tree check holds.

### Message - 2026-10-28T04:02:28Z - John Hoff

Progress (steps 1-5). Step 1: all six deployed SKILL.md files match their templates as normalized git blobs (`git hash-object --path`). Their working-tree copies are CRLF only because `core.autocrlf=true`, and both index entries are LF. Committed as cdb7505 "Sync bootstrapped skills after e019 redeployment". Steps 3-4: CLAUDE.md and AGENTS.md edited per Requirements 2-3 and review notes 1 and 3. Both now name `bootstrap` and `index rebuild` as CLI-only, describe the apply_patch-only hook and list the three skills; CLAUDE.md also has the bosses/rumors/numbering/branch domain model, the full module/template inventory and the workflow/tool-reference pair. Step 5 sourcebook audit: UPDATED world body; UPDATED `skills-authored-only-in-templates` body (template path now includes `world_planner`; summary unchanged, still accurate); UPDATED `crypts-and-commits` region summary and body (MCP layer, module list, tests split core/cli/mcp). UNCHANGED, current: `cli-mcp-parity` (already names both CLI-only exceptions), `workflow-doc-source-of-truth` (already describes the e019 pair and three skills), `console-best-practices` (no boss-edition dependence). Not in audit scope, left as is: CLAUDE.md's "demo-ui (Not yet added)" line, which is stale but outside CAC adoption.

### Message - 2026-10-28T04:04:01Z - John Hoff

CARRY-FORWARD (Requirement 7): the c001 rumors document is preserved here verbatim before its developer-requested deletion, followed by the docs/boss-edition.md audit result. Neither item is resolved by this encounter.

--- c001 rumors, verbatim ---
# c001-boss-edition rumors

## Campaign deletion guard is misdescribed in the campaign-manager skills (found during e019)

Both providers' `campaign-manager` templates say campaign deletion protects "linked/historical memberships, reverse boss claims and archived state". In code (`core/coupling.py`, `campaign_operation("delete")`), deletion is blocked only by a non-empty `bosses` list or a reverse boss claim; the archived-state check explicitly exempts `delete`, so an archived bossless campaign can be deleted. Decide whether archived campaigns should be protected from deletion (a core change) or whether the skill wording should drop "archived state" (a template change). workflow.md and tool-reference.md now describe the current code behavior.

## Long-running MCP server needs a restart to see new docs (found during e019)

A crypts-and-commits MCP server started before `tool-reference` was registered keeps listing the old docs set until it restarts. Worth a line in the migration guide's redeployment steps if it bites adopters.
--- end rumors ---

--- docs/boss-edition.md audit (Requirement 5) ---
Checked every section against workflow.md, tool-reference.md, branching-guide.md and migration-guide.md. Particular attention went to "Decisions established so far", "Scope and boundaries", "Splitting a boss", "Promotion contract", "Compatibility and release plan", "Implementation decision record (e001)" (including the workflow design examples) and "Remaining implementation details". Covered: numbered names/short refs and skill-only allocation; one current campaign per boss and multi-boss groups; draft-only membership; branch-agnostic endpoints; archive-as-flag and deferred archive restoration (workflow, branching-guide); available status retained after edits (workflow); splitting with explicit dependency reconciliation and no automatic rewrite (workflow); rejected-registration, registered-cancellation, legacy in-flight and pre-planning integration examples (workflow/branching-guide); optional PRs and direct merges; CI as the developer's choice; content-based stale-index detection with developer-run rebuild; effective branch defaults; schema 1 retained; no boss deletion operation; four-digit numbering; single-goal retries preserving groups. Gaps, i.e. decisions stated in none of the four guides: (a) "Decisions established so far": Git is foundational, and projects without a Git repository are out of scope. (b) "Decisions established so far" / "Scope and boundaries": multi-agent messaging, agent runtimes, schedulers and MCP Agent Mail belong outside CAC. Only partly covered: branching-guide states that no distributed claim or supervision is established. The file was removed with `git rm`; git history retains it.

### Message - 2026-10-28T04:06:30Z - John Hoff

Adoption verification (step 9) and gate (step 10). Rumors: `rumors_delete` succeeded, `rumors_get(c001)` now reports "Rumors for campaign 'c001-boss-edition' do not exist.", and `rumors_list` is empty. Docs: `docs_list` registers workflow, tool-reference, branching-guide and migration-guide. `docs_get` returns each one whole with no `next_cursor`: workflow 39,121 chars, tool-reference 29,032, branching-guide 12,577, migration-guide 20,528, all under the 64,000 docs budget. Skills: the deployed copies of all three skills match their templates (committed cdb7505) and match the ownership now described in CLAUDE.md, AGENTS.md and the world body. World settings: merge_target_branch=main, planning_branch=planning, schema_version=1. State: c001-boss-edition is open with no bosses; e001-e019 are completed and e020 is open. BRANCH GAP, disclosed and not fixed: the configured `planning` branch exists neither locally nor on origin (`git ls-remote --heads origin planning` returned nothing). Only c001-boss-edition and main exist. The developer must create `planning` before any boss planning under the recommended workflow. Remote state was observed through ls-remote at this time only. Gate: `pdm run pytest -q` 1564 passed; `ruff check .` all checks passed; `ruff format .` 284 files left unchanged (no fixes needed).
