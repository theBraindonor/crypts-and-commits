---
archived: false
campaign: c001-boss-edition
created_by: John Hoff
created_on: '2026-10-28T18:10:30Z'
depends_on:
- e025-record-gm-override-linking-c001-bosses
kind: scripted
name: e026-document-current-cac-usage
regions:
- crypts-and-commits
status: reviewed
updated_by: John Hoff
updated_on: '2026-10-28T18:12:16Z'
---

## Requirements

Update the public documentation so that a reader can learn to use `cac` as it exists on this branch now. That means standalone `rNNN` rumors (e023-e024), real boss records, and a full capture-to-vanquish path. The three files are the repository `README.md`, `docs/QUICKSTART.md` and the package README `packages/crypts-and-commits/README.md` (the PyPI long description). `docs/CHANGELOG.md` also records the rumor redesign. Every command, flag, tool name and behavior stated must match the shipped CLI/MCP surface. Where a doc and the code disagree, fix the doc.

1. **`README.md`**
   - Domain-model "Rumors" bullet (line 138): replace "one optional, freeform document per campaign" with the standalone model. A rumor is a numbered `rNNN` backlog note ("we think X should be done") from anywhere, with a free-text origin. It is triaged on planning into a boss (promote) or dismissed, never deleted.
   - Agent-skills paragraph (line 88): "rumor distillation" becomes rumor triage.
   - "How work flows" list: add the backlog step. Rumors captured anywhere are triaged on planning, and promoted rumors feed bosses.
   - Exploring section (lines 255-276): replace `cac rumors list` with `cac rumor list` and `rumors_*` with `rumor_*`. Add a short **usage example drawn from this repository's own live records**, using read-only commands that work here: `cac boss list`, `cac boss get b001`, `cac campaign get c001` (showing its linked bosses), `cac rumor list --status open` and `cac rumor get r001`. Explain in two or three sentences what the reader is seeing. c001 owns b001/b002 and will vanquish them on completion; r001-r003 are open backlog awaiting planning triage. Do not describe the GM override as a recommended practice. At most, note that c001's bosses were linked after it opened and point to c001/e025 for the record.
   - Dogfooding paragraph (line 202): now that bosses and rumors exist, state them as live content.
2. **`docs/QUICKSTART.md`**
   - Replace the campaign-scoped "Rumors" paragraph (lines 283-291) and the line 169 cross-reference with a new short walkthrough section, "Capture ideas as rumors", placed after "Capture future goals as bosses":
     - capture with `cac rumor create r001-slug --summary ... --origin ... --body-file ...` from any branch;
     - list and read with `cac rumor list [--status open]` and `cac rumor get r001`;
     - edit open rumors with `cac rumor update`;
     - on planning: renumber collisions with `cac rumor renumber` (open or dismissed only), promote to an existing unassigned boss with `cac rumor promote r001 b007` (two-step: create or refine the boss first), or dismiss with `cac rumor dismiss --message`;
     - `cac rumor reopen` undoes either; `cac rumor archive` retires resolved rumors; there is no delete;
     - similar rumors are not merged.
   - In "Pursue a boss with a campaign", add one sentence: select bosses into a campaign before opening it, because membership locks when the campaign opens.
   - Keep sections 1-3 and every other section intact apart from these fixes.
3. **`packages/crypts-and-commits/README.md`**: the "What's inside" object list (line 35) describes rumors as standalone `rNNN` backlog notes triaged into bosses, and the short-ref list gains `rNNN`. Keep absolute links.
4. **`docs/CHANGELOG.md`** (Unreleased - Boss Edition): replace the "Rumors (`rumors_*` / `cac rumors`): one optional freeform document per campaign" entry with the standalone rumor records (nine `rumor_*` tools / `cac rumor` commands, lifecycle, renumbering, `rumor` search type). Add `rNNN` to the short-references entry, and change "rumor distillation" (line 50) to rumor triage. No release number is chosen.
5. **Accuracy checks:**
   - every command and flag in the changed files appears in `pdm run cac <group> <command> --help`;
   - every read-only example runs successfully against this repository via `pdm run cac`;
   - every MCP tool name is registered;
   - relative links resolve;
   - mutating examples are validated by `--help` only, never executed.

Out of scope: packaged docs and skill templates (already current after e023-e024); code and tests; c001's completion, postmortem, merge or PR; creating a planning branch; triaging r001-r003; pushing.

## Rationale

The developer wants to pause before closing out c001 and first make sure the documentation teaches the current state of `cac`. Today the three public entry points and the changelog still describe the removed per-campaign rumors document and the `rumors_*` tools, so a reader following them would call commands that no longer exist. This repository now holds real goal records (b001/b002 linked to c001) and real rumors (r001-r003). Pointing the README's exploration section at them turns the dogfooded sourcebook into a concrete, runnable usage example of the boss and rumor workflow, without inventing sample data.

## Plan

1. Confirm branch `c001-boss-edition`, a clean tree, and sync with `origin`.
2. Collect the ground truth: `pdm run cac rumor --help` and each subcommand's `--help`, `cac boss --help`, `cac campaign get --help`. Run the read-only examples to capture real output for the README explanation.
3. Edit `README.md` per Requirement 1.
4. Edit `docs/QUICKSTART.md` per Requirement 2.
5. Edit the package README per Requirement 3.
6. Edit `docs/CHANGELOG.md` per Requirement 4.
7. Run the Requirement 5 accuracy checks. Grep the four files case-insensitively for `rumors_`, `cac rumors`, `per campaign`, `distill` and `bosses/rumors`, and review each hit by hand.
8. Run `pdm run pytest -q`, `pdm run ruff check .` and `pdm run ruff format .` (no Python changes are expected; docs tests may still check public files).
9. Record the results with `encounter_record_message`.
10. Commit as "Document current cac usage with standalone rumors (e026)". Do not push.

## Verification

- `README.md` describes standalone rumors, includes the backlog step in "How work flows", and its exploration section has a working example of this repo's bosses, campaign link and rumors using `cac rumor`.
- `docs/QUICKSTART.md` has a "Capture ideas as rumors" walkthrough covering capture, list/get, update, renumber, promote, dismiss, reopen and archive; it says membership locks at open; no campaign-scoped rumors text remains.
- The package README and `CHANGELOG.md` describe standalone rumors and `rNNN`.
- The step-7 grep finds no stale reference; every command, flag and tool exists; every read-only example runs; links resolve.
- Only the four documentation files and the sourcebook record change (`git diff --stat`).
- `pdm run pytest -q` passes; `ruff check .` reports zero errors; `ruff format .` changes nothing.
- The developer reviews the doc diffs and confirms completion.

## Log

### Review - 2026-10-28T18:12:16Z - John Hoff

Independent review PASS-WITH-NOTES. Applicable lore: clean-tests-and-lint (world), cli-mcp-parity, console-best-practices, skills-authored-only-in-templates, workflow-doc-source-of-truth (crypts-and-commits region). The plan is docs-only: README.md, docs/QUICKSTART.md, docs/CHANGELOG.md and packages/crypts-and-commits/README.md, with code, skill templates and packaged docs explicitly out of scope. So cli-mcp-parity, console-best-practices, skills-authored-only-in-templates and workflow-doc-source-of-truth are not triggered, and nothing in the plan conflicts with them. clean-tests-and-lint is honored by step 8 and the Verification gates. Spot-check: the stale rumors_/cac rumors/distill text exists at the cited locations (README 'distillation' is line 89, not 88). Notes for execution: (a) Cross-check the new QUICKSTART lifecycle and guard claims against docs_get workflow and tool-reference, not just --help. These are the renumber open/dismissed-only rule, promote to an unassigned boss, no delete, reopen semantics and membership locking at campaign open. (b) Verify MCP tool names against the registered tool set, and verify the 'rumor' search type claim. (c) Step 1's clean-tree check must account for the untracked e026 record. (d) Treat cited line numbers as approximate and hand-review step-7 grep hits.
