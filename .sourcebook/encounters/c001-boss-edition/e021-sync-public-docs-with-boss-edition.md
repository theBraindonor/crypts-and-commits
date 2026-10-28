---
archived: false
campaign: c001-boss-edition
created_by: John Hoff
created_on: '2026-10-28T04:09:28Z'
depends_on:
- e020-adopt-boss-edition-workflow-in-this-repo
kind: scripted
name: e021-sync-public-docs-with-boss-edition
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-10-28T13:28:48Z'
---

## Requirements

Bring the three public-facing documents in line with the Boss Edition features shipped in c001 (e001-e020) before the campaign's implementation PR into `main`: the repository `README.md`, `docs/QUICKSTART.md`, and the package README `packages/crypts-and-commits/README.md`, which is the PyPI long description (`readme = "README.md"` in `packages/crypts-and-commits/pyproject.toml`). Every command, flag, tool name and behavior these files state must match the shipped CLI/MCP surface. Where a doc and the code disagree, fix the doc; never change behavior to fit the doc.

1. **`README.md`**
   - "Exploring this repository's sourcebook": add `cac boss list` and `cac rumors list` to the CLI example block and `boss_list`/`rumors_*` to the MCP sentence. Change the `cac encounter list` example to `cac encounter list --campaign c001` with an accurate comment, because that example otherwise fails when no campaign is open, which will be the state after c001 completes.
   - "Domain model & personas": mention rumors (one optional document per campaign) and numbered names with short refs (`bNNN`, `cNNN`, `cNNN/eNNN`). Note that a campaign pursues zero, one or many bosses.
   - Add a short "How work flows" passage (a few sentences, or one short list): capture goals as bosses → select them into a draft campaign → open it on its own execution branch → reviewed encounters → complete, vanquishing the selected bosses. State that the planning / assignment / execution branch workflow is skill guidance with branch-agnostic endpoints, and link the Branching Guide instead of restating it.
   - Dogfooding paragraph: include bosses and rumors in the list of live sourcebook content.
   - Keep the pitch ("Why Crypts and Commits"), demo-app instructions, repository layout and license sections unchanged apart from these fixes.
2. **`docs/QUICKSTART.md`**
   - Branch settings: say plainly that the configured `planning` branch, and the merge target if it isn't the existing default branch, must be created by the developer under their Git policy before the recommended planning workflow is used. CAC never creates or switches branches.
   - Upgrade section: after upgrading the library, restart or reconnect long-running MCP servers and agent sessions so they load the new package. A server started on the old version keeps serving the old tools and docs list. (This carries forward the e019 finding recorded in e020's log.)
   - Restructure the "Capture future goals as bosses", "Discover the next goal", "Use short references" and "Pursue a boss with a campaign" sections from dense guard-rule prose into a readable walkthrough. Keep every feature the guide currently covers: create/update/make-available/dependencies/withdraw/reactivate/archive, candidates and cursor continuation, short refs and literal create names, promotion and multi-boss `--boss`, open-on-execution-branch, reactivation for PR feedback, archive on planning, and rumors. Keep the command examples (valid ones unchanged; any invalid one corrected). Move exhaustive guard detail to links to `cac docs get workflow` / `tool-reference` rather than deleting facts outright, and keep any guard a first-time user would trip over.
   - Keep sections 1-3 (install, bootstrap, hand-off) structurally intact.
3. **`packages/crypts-and-commits/README.md`**
   - Light consistency pass. Split the run-on Quickstart paragraph into short sentences or a list (bootstrap creates the sourcebook, registers the MCP server, deploys the three skills; bootstrap is developer-only). Make sure the object list, skill names and doc names match the other two files. Keep the GitHub links absolute, since this text renders on PyPI.
4. **Accuracy checks.** Verify every command and flag shown in all three files against `pdm run cac <group> <command> --help`. Verify every MCP tool name named against the registered tool set, and every doc name against `docs_list`. Verify behavior claims (e.g. bootstrap re-run semantics, hook scope, default branch values) against `tool-reference`/`workflow` or the source. Relative links in `README.md`/`QUICKSTART.md` must resolve to existing files.

Out of scope: packaged docs (`templates/docs/*.md`), skill templates, `cac` source and tests; `docs/CHANGELOG.md` (updated in e020); the version number, release tag and publishing; the demo-api/demo-ui package READMEs; resolving the two design decisions missing from the packaged guides or the campaign-deletion wording mismatch recorded in e020; creating any branch; pushing.

## Rationale

These three files are the first thing a new adopter reads, on GitHub and on PyPI. Earlier encounters (e002-e016) appended feature notes to them incrementally, so they are broadly current but uneven. The README's sourcebook-exploration example omits bosses and rumors and will break once no campaign is open. Nothing public explains the boss → campaign → encounter flow at a glance. The quickstart never tells a developer to create the planning branch its own defaults assume; this very repository hit that gap in e020. Its goal and campaign sections have grown into contract-style prose that duplicates `tool-reference` and is hard to follow. Fixing these before the implementation PR means the Boss Edition release ships with an accurate entry point, while the packaged guides stay the authoritative detail.

## Plan

1. Confirm the branch (`c001-boss-edition`) and a clean working tree.
2. Collect the ground truth: run `pdm run cac --help` and `--help` for each command group/command the docs mention (`world`, `boss`, `campaign`, `encounter`, `rumors`, `prime`, `docs`, `index`, `bootstrap`). Read the registered MCP tool names from `mcp/server.py` / the module list and the doc names from `docs_list`.
3. Edit `README.md` per Requirement 1.
4. Edit `docs/QUICKSTART.md` per Requirement 2. Restructure the boss/campaign sections, keeping a checklist of every feature and command currently covered, and confirm none is dropped.
5. Edit `packages/crypts-and-commits/README.md` per Requirement 3.
6. Run the Requirement 4 accuracy checks across all three files. Run each read-only example command (`world get`, `lore list`, `region list`, `campaign list`, `encounter list --campaign c001`, `boss list`, `rumors list`, `docs get ...`, `prime get`, `boss candidates`, short-ref `get`s) against this repository through `pdm run cac` to confirm it runs. Validate mutating examples by `--help` only, never by executing them. Check that every relative link resolves.
7. Record the feature checklist and accuracy results with `encounter_record_message`.
8. Run `pdm run pytest -q`, `pdm run ruff check .` and `pdm run ruff format .` (no Python changes are expected; apply any fixes).
9. Commit the three docs together with the e021 sourcebook record as "Sync public docs with Boss Edition (e021)". Do not push.

## Verification

- `README.md` lists bosses and rumors in its sourcebook-exploration block, and that block's encounter example passes `--campaign c001`. It mentions rumors and short refs in the domain model, has a short boss → campaign → encounter flow linking the Branching Guide, and keeps its other sections intact.
- `docs/QUICKSTART.md` tells the developer to create the planning branch (and the merge target if needed), and tells them to restart MCP servers/sessions after an upgrade. Its boss/campaign sections read as a walkthrough, and the recorded checklist shows every previously covered feature and command still present or explicitly linked.
- `packages/crypts-and-commits/README.md` has no run-on Quickstart paragraph, matches the other two files' object/skill/doc names, and keeps absolute links.
- Every command and flag in the three files appears in the matching `--help` output; every read-only example ran successfully here; every MCP tool and doc name exists; every relative link resolves.
- No file outside the three docs and the sourcebook changes (`git status` / `git diff --stat`), and the working tree is clean after the commit.
- `pdm run pytest -q` passes; `ruff check .` reports zero errors; `ruff format .` leaves files unchanged.
- The developer reviews the doc diffs and confirms completion.

## Log

### Review - 2026-10-28T13:04:11Z - John Hoff

Independent review PASS-WITH-NOTES. Applicable lore: clean-tests-and-lint, cli-mcp-parity, console-best-practices, skills-authored-only-in-templates, workflow-doc-source-of-truth. clean-tests-and-lint is honored: Plan step 8 and Verification require pytest passing and ruff check/format clean, with no bypasses. The plan changes documentation only (README.md, docs/QUICKSTART.md, packages/crypts-and-commits/README.md) and makes no change to cli/, mcp/, core/ or skill templates, so cli-mcp-parity, console-best-practices, skills-authored-only-in-templates and workflow-doc-source-of-truth are not triggered. Its rule to fix the doc and never the behavior, its accuracy checks against --help, registered MCP tools, docs_list and the packaged guides, and its move of guard detail into links to workflow/tool-reference all fit the single-owner rule. Read-only examples run through the sanctioned cac CLI, mutating examples are checked by --help only, nothing reads .sourcebook directly, and there is no push and no branch creation. Notes: (1) the --campaign c001 short-ref form of encounter list is unverified at review time and must be confirmed in step 6; (2) the out-of-scope note about the campaign-deletion wording mismatch is stale since e022 fixed it, so the docs should follow the corrected guide wording; (3) completeness of the QUICKSTART feature checklist is enforced only by the recorded step-7 checklist; (4) README.md and docs/QUICKSTART.md fall outside the assigned region's path, so only world lore governs them.

### Opened - 2026-10-28T13:05:21Z - John Hoff

Opened with developer approval. Working tree clean apart from this encounter's own review record. Will handle reviewer notes: verify encounter list --campaign c001 by execution, use e022-corrected deletion wording if any doc describes it, and build the QUICKSTART feature checklist from the current file before restructuring.

### Message - 2026-10-28T13:11:25Z - John Hoff

Plan steps 2-6 done. Feature checklist, built from the pre-edit QUICKSTART boss/campaign sections; every item is still present in the rewrite. Bosses: create (literal full name, --body-file, --summary at most 500 chars, editor fallback), get, update, make-available regardless of prerequisites, assign/unassign-dependency with graph validation, list, withdraw, reactivate, archive (unassigned withdrawn or externally completed roadmap goals), list --include-archived, edit/freeze rules, archived names retained and readable, no delete or restore, empty storage provisioned on first create, skills allocate numbers and endpoints never do, legacy names valid, world-planner roadmap capture plus migration guide, boss_* MCP parity, boss search and active-boss prime, links to workflow and tool-reference. Candidates: JSON page, --cursor continuation, eligible/not_ready/blocked/excluded semantics, archived vanquished prerequisites count, counts, healthy/diagnostics, numeric order is not priority, hydrate with get, does not select work or prove merge. Short refs: b001/c001/c001/e001, bare e001 context, all 5 examples kept, qualified override, conflicting-campaign error, archived resolve, duplicate ambiguity, identity metadata, literal create names, canonical dependencies, no allocation/rename/git/migrate/assign, tool-reference link. Campaign: publish planning to merge target, eligibility, allocation, assignment branch, assign-campaign and campaign get examples, promotion creates a draft only, multi-boss --boss (now with an explicit campaign create example), integrate registration, open on the execution branch after authorization, bossless campaigns skip registration, encounter approvals, completion vanquishes, abandonment releases, Branching Guide local-merge/PR (now linked), reactivate example, follow-up encounters, archive on synchronized planning, reassigned boss untouched, rumors create/update and distillation, boss_assign_campaign/campaign_reactivate MCP parity, read-only retries, ownership diagnostics and recovery, no automatic Git. Deviations: (1) per reviewer note 2, the old line "Origin/reverse links prevent campaign deletion." was replaced with the e022-corrected rule (deletion only with an empty bosses list and no boss claim; archiving does not protect a bossless campaign). (2) This repo has no boss or rumors records yet (boss list and rumors list are both empty), so the README dogfooding paragraph says bosses and rumors are "recorded as goals and discoveries arise" rather than claiming them as existing content. (3) The README now says "seven object types" because Rumors was added to the list. Accuracy: every flag used (boss create/update --body/--body-file/--summary, list --include-archived, candidates --cursor, assign-campaign --body-file, campaign create --boss, reactivate --message, encounter list --campaign, rumors create --campaign --body-file) appears in --help. A scripted check confirmed all 28 cac group/command pairs exist and found 0 broken relative links. 17 read-only examples ran with exit code 0, including encounter list --campaign c001 (reviewer note 1), boss list, rumors list, boss candidates, campaign get c001, encounter get c001/e001, and docs get for workflow, tool-reference, branching-guide and migration-guide. MCP tools named in the docs all exist in the registered set; docs_list lists all four doc names.

### Completed - 2026-10-28T13:28:48Z - John Hoff

Verification passed: all three docs updated per Requirements; accuracy checks (flags, 28 command pairs, links, 17 read-only examples, MCP tool and doc names) clean; pytest 1564 passed, ruff check/format clean; only the three docs and this record changed. Doc changes committed in ccff94b. Developer reviewed and confirmed completion.
