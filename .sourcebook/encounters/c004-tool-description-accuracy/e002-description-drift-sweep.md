---
archived: false
campaign: c004-tool-description-accuracy
created_by: John Hoff
created_on: '2026-11-21T06:04:40Z'
depends_on: []
kind: scripted
name: e002-description-drift-sweep
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-11-21T06:19:27Z'
---

## Requirements

Audit every agent-facing tool description against its owning contract and fix drift, completing b004's second success condition ("any other description/help drift found is fixed in both surfaces").

1. **Scope of the audit.** All 85 `@mcp.tool()` docstrings in `packages/crypts-and-commits/src/cac/mcp/` (boss 13, campaign 12, docs 2, encounter 15, index 2, lore 12, prime 2, region 7, ruling 8, rumor 9, world 3). Also the matching `cac` CLI help: the Typer group `help=` text, command docstrings and option/argument `help=` strings in `src/cac/cli/`. Each is compared against its section of `src/cac/core/templates/docs/tool-reference.md`, the contract owner.
2. **What counts as drift:** a description that omits a capability the tool has (a parameter, filter value, accepted reference form or result field an agent would need), or states something false (wrong statuses, wrong defaults, wrong guard, a stale type or field list). The other case is an MCP/CLI pair that disagrees on a fact. Differences in length or style are not drift. The MCP description may stay terser than the CLI help, and neither must restate tool-reference in full.
3. **Fix in both surfaces.** Every confirmed drift is corrected in the MCP docstring and the CLI help together (`cli-mcp-parity`). Where tool-reference.md itself is wrong or less specific than the code, correct tool-reference.md too, since it stays the contract owner (`workflow-doc-source-of-truth`). Corrections are wording only. The tool's behavior, signatures, defaults, results and error messages do not change.
4. **Agent-facing docs and skill templates are checked, not swept.** Check the review-flagged areas for outdated search or description wording: the packaged skill templates (`src/cac/core/templates/skills/{claude,codex}/*/SKILL.md`), `planning-workflow.md`, `development-workflow.md` and `migration-guide.md`. A real factual error in a skill template is fixed in **both** flavors' templates only, never in the deployed `.claude/skills/` or `.agents/skills/` copies (`skills-authored-only-in-templates`). Redeploying via `cac bootstrap init` is the developer's job. A change to a phase guide that touches a shared rule keeps the guides' synchronized copies identical.
5. **Out-of-scope findings become rumors.** These include behavior bugs, missing tools, contract design questions and anything that would change behavior. They are captured with `rumor_create` (origin `c004/e002`), not fixed here.
6. **Known seed findings** from pre-draft scanning, to confirm or dismiss during the audit:
   - The `cac prime` Typer group help says prime replaces "world/lore/region/campaign/encounter reads". The bundle also carries active bosses and recorded rulings, and `cac prime get` already says so.
   - The `docs_get` MCP description routes `development-workflow` "for campaigns/encounters/gates". This needs confirming against the docs registry summaries and the world-manager skill's routing wording.

## Rationale

e001 fixed the most visible case. b004's rationale is that descriptions drift as features land, and c001–c003 added or reshaped many tools: bosses with provenance, candidates and short references; rumors; rulings; and the phase-split docs. Agents read tool descriptions on every call, but tool-reference.md only on demand, so a stale description means an agent never learns a capability exists. Auditing against the contract owner, fixing both surfaces together and spinning off anything behavioral keeps this encounter a pure accuracy pass that can be reviewed.

## Plan

All paths are under `packages/crypts-and-commits/`.

1. **Build the audit inventory.** Produce a per-tool pairing of MCP name, CLI command and tool-reference.md section for every MCP tool and CLI command. The two CLI-only commands, `bootstrap init` and `index rebuild`, are listed as intentionally MCP-less per `cli-mcp-parity`.
2. **Audit domain by domain** in this order: world, lore, region, prime, docs, index, boss, campaign, encounter, rumor, ruling. For each tool, compare the MCP docstring, the CLI help (rendered with `pdm run cac <module> <command> --help` at a fixed width) and tool-reference.md against the Requirement 2 criteria. Where tool-reference.md and the description disagree, check the core implementation to settle which is right.
3. **Record findings before fixing.** After each domain group, append a findings list to this encounter with `encounter_record_message`. Each entry gives the tool, the drift, the evidence, and whether it's fixed here or spun off as a rumor. "No drift" is also recorded per domain, so the audit is visibly complete.
4. **Fix confirmed drift** in `mcp/<domain>.py` and `cli/<domain>.py`, and in tool-reference.md where it is the wrong or less specific side. Help text avoids `[...]` brackets, because rich renders them as markup.
5. **Check docs and skill templates** for the patterns found in steps 2–4 and the review-flagged search wording (Requirement 4). Fix real factual errors in the packaged templates, in both flavors. Record what was checked.
6. **Capture out-of-scope findings** as rumors. Allocate numbers from every `rumor_list(include_archived=True)` page; numeric max+1.
7. **Tests.** Where a fix corrects a fact that a test can pin cheaply and that is likely to drift again, add a focused assertion in the matching `tests/mcp/` or `tests/cli/` module. Examples are an enum of statuses or types named in a description. Use e001's drift-guard style, deriving expected values from `cac.core.config` rather than hard-coding them. Do not add tests that assert prose wording.
8. Run `pdm run pytest -q`, `pdm run ruff check .` and `pdm run ruff format .`, and fix anything reported.

## Verification

- The encounter log contains per-domain findings covering all 11 MCP domains and their CLI counterparts, each finding marked fixed or spun off as a rumor, and an explicit "no drift" for clean domains.
- Each fixed finding is visible in both surfaces: the MCP docstring, and the CLI help rendered with `pdm run cac <module> <command> --help`. tool-reference.md agrees with both.
- Skill-template changes, if any, appear in both the claude and codex template flavors, and the deployed `.claude/skills/` and `.agents/skills/` copies are untouched in `git diff`.
- `git diff` shows only docstrings, help strings, packaged doc/template text and tests. No changes to signatures, defaults, logic or error messages.
- Any rumors created are listed in the completion message.
- `pdm run pytest -q` passes; `pdm run ruff check .` reports zero errors; `pdm run ruff format .` produces no diffs (`clean-tests-and-lint`).

## Log

### Review - 2026-11-21T06:08:36Z - John Hoff

Independent lore review of c004/e002 (scripted) against clean-tests-and-lint, cli-mcp-parity, console-best-practices, skills-authored-only-in-templates and workflow-doc-source-of-truth: PASS-WITH-NOTES. The Plan is a wording-only accuracy pass with behavior explicitly frozen. Every drift fix goes into both the MCP docstring and the CLI help (parity kept, and bootstrap init and index rebuild correctly listed as the only MCP-less commands). tool-reference.md stays the contract owner and is corrected where it is wrong, with core settling disputes. Skill fixes go only into both template flavors, the developer redeploys, and `git diff` confirms the deployed copies are untouched. Phase-guide shared-rule copies stay synchronized. Bracket-free help text is respected, and the pytest/ruff gate is in step 8 and Verification. The MCP tool inventory (85) matches the source. Notes: (a) if the docs_get routing wording changes, also check workflow.md and the tool-reference docs_get section for matching phrasing; (b) if a docs registry summary string in core/docs.py needs correcting, either allow that core string explicitly in the Verification diff rule or spin it off as a rumor; (c) keep the step-7 drift-guard tests to config-derived values, not prose.

### Opened - 2026-11-21T06:11:00Z - John Hoff

Opened with developer approval. Review note (b) resolved: wording fixes may reach the docs registry summary strings in core/docs.py.

### Message - 2026-11-21T06:11:07Z - John Hoff

Deviation from the Verification diff rule, approved by the developer (ruling c004-e002-docs-registry-summaries-in-scope): summary strings in core/docs.py's _DOCS registry may receive wording-only fixes. Review notes (a) and (c) will be followed: matching routing phrasing is checked in workflow.md and tool-reference.md, and drift guards stay config-derived.

### Message - 2026-11-21T06:13:29Z - John Hoff

Audit findings, part 1 (inventory, world, lore, region, prime, docs, index).

Inventory: 85 MCP tools; 87 CLI commands = 85 paired + bootstrap init + index rebuild (intentionally MCP-less). Command-level parity is complete.

- world: drift (omission). world_set's MCP description omits that the branch settings (merge_target_branch, planning_branch) are set through it and that any string is accepted without branch-name validation; the CLI key help names them. FIX in MCP (CLI already names keys; add the no-validation note to both).
- lore: drift (false statement). lore_update's MCP description says it is "regenerating its summary", but the caller supplies the summary. The CLI update help says only "Update ... body" although the summary is replaced too. FIX both surfaces to "replace body and summary together" (tool-reference's wording). The other 11 lore tools: no drift.
- region: drift, the same as lore for region_update. FIX both. The other 6 region tools: no drift.
- prime: drift (seed 1 confirmed). The cac prime group help lists only world/lore/region/campaign/encounter reads; the bundle also carries active bosses and recorded rulings. FIX the CLI group help. prime_get and applicable-lore descriptions: no drift. See the skill finding in part 2 about applicable-lore paging.
- docs: drift (seed 2, broader). The docs_get MCP description routes only planning-workflow, development-workflow and workflow; tool-reference, branching-guide and migration-guide are never named. FIX MCP docs_get, plus the CLI docs get help. The registry summaries in core/docs.py are accurate, so no change there (ruling c004-e002-docs-registry-summaries-in-scope is not exercised). workflow.md routing phrasing is accurate.
- index: no drift after e001. index_status is accurate.

Out of scope, not fixed: core docstrings for lore.update_lore and region.update_region repeat "regenerating its summary", and core encounter.py's region-mutation error docstring says "'draft'/'reviewed'" although the guard is draft-only. These are internal core docstrings, not agent-facing, and are outside ruling scope; they are noted here only.

### Message - 2026-11-21T06:13:42Z - John Hoff

Audit findings, part 2 (boss, campaign, encounter, rumor, ruling, docs and skill templates).

- boss: drift (omission, minor). boss_create's MCP description omits that a new boss starts proposed; the CLI says "Create a proposed boss". FIX MCP. The other 12 boss tools: no drift. Wording differs between surfaces (assign-campaign, record), but there is no factual disagreement.
- campaign:
  - (C1) The `cac campaign set-bosses` command has no description of its own, only the shared identity footer. FIX the CLI to describe atomic draft-only replacement, with omitting --boss clearing the set.
  - (C2) campaign_delete's MCP description says "origin history ... protect deletion", which is opaque. The CLI delete help states no guard at all. Core (coupling.campaign_operation "delete") refuses when the campaign has any current or historical bosses membership or a boss still claims it. FIX both.
  - (C3) The CLI complete, abandon and archive help omit the boss coupling that their MCP descriptions state: complete vanquishes linked bosses, abandon releases current links but keeps historical membership, archive moves current bosses. FIX the CLI.
  - (C4) The CLI create help, "Create a new campaign file", omits that it starts draft and can select eligible bosses with --boss. FIX the CLI.
  - Others (get, list, open, pause, reactivate, update): no drift.
- encounter:
  - (E1) The encounter_assign_region / encounter_unassign_region MCP descriptions and CLI command help omit the draft-only guard (core _REGION_MUTATION_STATUSES = draft). It is stated only in the CLI group help. FIX both.
  - (E2) The CLI delete help omits the guard that it fails while another encounter depends on the target; MCP states it. FIX the CLI.
  - (E3) The CLI open help omits the guard that it fails until every direct dependency is completed; MCP states it. FIX the CLI.
  - Others: no drift.
- rumor: drift (omission). rumor_list's MCP description does not name its status filter values (open, promoted, dismissed); the CLI does, and ruling_list's MCP description names its own. FIX MCP, with a config-derived guard test for RUMOR_STATUSES, and one for ruling_list against RULING_STATUSES. Others: no drift.
- ruling: no drift.
- docs and skill templates (Requirement 4): planning-workflow.md, development-workflow.md, migration-guide.md and branching-guide.md have no stale search/description wording. The skill templates' index_search usage is accurate. DRIFT in both world_manager skill templates (claude and codex): they document `prime_applicable_lore(encounter, campaign, cursor)` as "paged under the response budget; pass the cursor ...", but the MCP tool takes no cursor and returns the full list. Only the CLI pages, as tool-reference.md says correctly. FIX both templates' wording to match. Whether the MCP tool should page is a contract/behavior question, so SPIN OFF as rumor r005.

### Message - 2026-11-21T06:18:55Z - John Hoff

Fixes applied: world_set (MCP+CLI no-validation note); lore_update and region_update (both surfaces: body and summary together); prime CLI group help (adds boss/ruling); docs_get MCP and docs get CLI (all 6 registered docs); boss_create (starts proposed); campaign C1-C4 (set-bosses description, delete guard in both, CLI complete/abandon/archive boss coupling, CLI create draft and --boss); encounter E1-E3 (region draft-only guard in both, CLI delete and open guards); rumor_list statuses. Both world_manager skill templates (claude and codex) now say MCP prime_applicable_lore takes no cursor and returns the whole set, and only the CLI pages; the deployed .claude/.agents copies are untouched. tool-reference.md gained the campaign lifecycle boss coupling and delete guard, plus the encounter region/dependency draft-only guard, so it is at least as specific as the descriptions. Drift-guard tests added: rumor_list vs config.RUMOR_STATUSES, ruling_list vs config.RULING_STATUSES, and docs_get vs the docs registry (hyphen-aware boundaries). Discovered, out of scope: core/references.py:306 appends the identity footer without dedenting, so wrapped docstring lines on reference-taking tools render with stray 4-space runs in CLI help and MCP descriptions. This predates c004, and the new multi-line docstrings inherit it. SPUN OFF as rumor r006-reference-docstring-indent-leak.

### Completed - 2026-11-21T06:19:27Z - John Hoff

Verification passed, confirmed by the developer. The audit covered all 11 MCP domains and their CLI counterparts, with findings logged per domain. All confirmed drift is fixed in both surfaces, and tool-reference.md is updated where it was less specific. Both world_manager skill templates are corrected; the deployed copies are untouched. Drift guards were added for rumor_list and ruling_list statuses and for the docs_get registry names. Rumors created: r005-applicable-lore-mcp-paging, r006-reference-docstring-indent-leak. Full suite: 1727 passed; ruff check and ruff format --check are clean.
