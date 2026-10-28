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
status: draft
updated_by: John Hoff
updated_on: '2026-10-28T04:09:29Z'
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
