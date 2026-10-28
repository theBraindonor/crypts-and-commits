---
archived: false
campaign: c001-boss-edition
created_by: John Hoff
created_on: '2026-10-28T16:48:22Z'
depends_on:
- e023-promote-rumors-to-standalone-records
kind: scripted
name: e024-align-guides-and-repo-instructions-with-standalone-rumors
regions:
- crypts-and-commits
status: reviewed
updated_by: John Hoff
updated_on: '2026-10-28T16:50:22Z'
---

## Requirements

Bring the remaining project text that still describes the removed per-campaign rumors document into line with the standalone `rNNN` rumor records shipped in e023. The model is defined in `templates/docs/workflow.md` ("Rumors" section and planning handoff) and its contracts in `templates/docs/tool-reference.md` ("Rumors"). These two owning docs are the source of truth for this encounter and are **not** changed here, unless a contradiction is found; any contradiction is logged and fixed in the owning doc in this same change.

1. **`templates/docs/branching-guide.md`** (packaged guide):
   - The branch-role table (line 24: planning does "rumor distillation"; line 26: the execution branch holds "rumors"). Planning does rumor **triage** (renumbering, promotion, dismissal, archival). Any branch, execution included, may capture rumors.
   - Lines 29 and 37-38: "distilling rumors" / "rumor distillation" become triage wording.
   - Worked example step 5 (lines 110-114): replace the `rumors_create`/`rumors_update`/`rumors_get` and `cac rumors ... --campaign c012` text and the "one freeform document per campaign" claim. The new example captures a numbered rumor with `rumor_create` / `cac rumor create r00N-slug --summary ... --origin "c012 execution" --body-file ...`, allocated from `rumor_list(include_archived=True)` on that branch, without expanding the chosen goals.
   - Worked example step 7 (lines 123-128): after synchronizing planning, world-planner triages integrated open rumors. It renumbers any collision with `rumor_renumber` (open or dismissed only), promotes to a developer-selected unassigned boss with `rumor_promote` (boss created or refined first), or dismisses with `rumor_dismiss`, and archives resolved rumors. Rumors are never deleted. Keep the existing "bosses owned by later attempts remain untouched" point, and reword "Rumors stay live" accordingly.
   - If the guide's collision-checkpoint text lists the record types checked after integration, add rumor numbers: rumor collisions are accepted and fixed by renumbering on planning, and promoted rumors keep their numbers.
2. **`templates/docs/migration-guide.md`** (packaged guide): the adoption table rows at lines 123 and 127 and the quoted instruction text at line 134 become triage wording. Line 127 changes from "capture execution discoveries with rumors operations; distill integrated rumors" to: capture discoveries from anywhere as standalone rumors (`rumor_create`), and triage integrated rumors on planning with world-planner into selected goals or dismissals, without deletion or scope expansion. No migration step is added: rumors were never released, so no adopting project holds per-campaign rumors documents.
3. **This repository's `CLAUDE.md`** (`AGENTS.md` has no rumor references):
   - Lines 9, 13, 51, 54, 63, 76, 79, 90 and 91 are updated:
     - the dogfooded-content list;
     - the MCP tool families (`rumor_*`) and CLI groups (`cac rumor`);
     - the `core/` and `mcp/` module lists (`rumor.py`);
     - `references.py` short refs (add `rNNN`);
     - the domain-model entry, which replaces `bosses/rumors/<campaign>.md` with a `rumors/<name>.md` entry describing the open/promoted/dismissed lifecycle, the boss link stored only on the rumor, renumbering of open/dismissed rumors on planning, archiving under `archive/rumors/`, and no delete;
     - the numbered-names paragraph (add `r001-slug` / `rNNN`);
     - the world-planner and campaign-manager skill descriptions (triage versus capture).
   - Keep every other sentence unchanged.
4. **The `crypts-and-commits` region record body:** its Architecture-rule paragraph names `rumors.py` as a core module. Change it to `rumor.py` with `region_update`. The summary does not mention rumors and stays unchanged.

Out of scope: `workflow.md`/`tool-reference.md` (except a contradiction fix as above); skill templates and deployed skill copies (done in e023); code and tests; the public docs `README.md`, `docs/QUICKSTART.md`, the package README and `docs/CHANGELOG.md` (e025); bootstrap; pushing.

## Rationale

e023 changed the code, the owning docs and the skills together, but deliberately left the two packaged guides and this repo's own instructions for a follow-up. They still teach `rumors_*` tools that no longer exist and a per-campaign document model, so an agent following the Branching Guide's worked example, or this repo's `CLAUDE.md`, would call missing tools. The guides ship to every adopting project, and `CLAUDE.md` primes every session here. The region record is session-priming context too. Fixing all four together closes the last stale descriptions before the public-docs sync and the c001 PR.

## Plan

1. Confirm branch `c001-boss-edition`, a clean tree, and that it is in sync with `origin`.
2. Read the `workflow.md` Rumors and planning-handoff sections and the `tool-reference.md` Rumors section (via `cac docs get`) as the reference wording.
3. Edit `branching-guide.md` per Requirement 1, keeping its existing example campaign (`c012-search-tools`) and step numbering.
4. Edit `migration-guide.md` per Requirement 2.
5. Edit `CLAUDE.md` per Requirement 3.
6. Update the region body per Requirement 4 with `region_update` (MCP), replacing only `rumors.py`.
7. Check:
   - Grep case-insensitively for `rumors_`, `cac rumors`, `bosses/rumors`, `distill` and `per campaign` across `templates/`, `CLAUDE.md` and `AGENTS.md`. Zero stale hits are expected; review every remaining `rumor` hit by hand.
   - Confirm every `cac rumor ...` command and `rumor_*` tool named in the edited files exists (`--help` and the registered tool set).
   - Confirm relative links still resolve.
   - Re-read the region body with `region_get`.
8. Run `pdm run pytest -q`, `pdm run ruff check .` and `pdm run ruff format .`. Docs tests include size caps; if a guide exceeds its cap, condense rather than raise it.
9. Record the results with `encounter_record_message`.
10. Commit as "Align guides and repo instructions with standalone rumors (e024)". Do not push. The packaged guides are served by `docs_get`, so ask the developer to restart the MCP server if they want the running session to serve the new guide text.

## Verification

- `branching-guide.md` and `migration-guide.md` describe rumor capture from any branch and triage on planning, name only `rumor_*` tools and `cac rumor` commands, and contain no per-campaign document description. The worked example's capture and planning steps use the new commands.
- `CLAUDE.md` names `rumor.py`, `rumor_*`, `cac rumor`, `rNNN` and the `rumors/<name>.md` domain entry, with no `bosses/rumors`, `rumors_*` or "distillation" wording left.
- `region_get crypts-and-commits` shows `rumor.py`.
- The step-7 grep finds no stale reference; every named command and tool exists; links resolve.
- No file outside the two guides, `CLAUDE.md` and the sourcebook changes (`git diff --stat`).
- `pdm run pytest -q` passes; `ruff check .` reports zero errors; `ruff format .` changes nothing.
- The developer confirms completion.

## Log

### Review - 2026-10-28T16:50:22Z - John Hoff

Independent review: PASS-WITH-NOTES. Applicable lore is clean-tests-and-lint, workflow-doc-source-of-truth, skills-authored-only-in-templates, cli-mcp-parity and console-best-practices. clean-tests-and-lint is honored: pytest and ruff are gated, and docs size caps are met by condensing. workflow-doc-source-of-truth is honored: the plan makes no mcp/cli/core/skill-template change, treats workflow.md and tool-reference.md as the reference, and fixes any contradiction in the owning doc in the same change. The required rumor wording matches both docs (any-branch capture, triage on planning, promote to an unassigned proposed/available boss, renumber only open/dismissed, archive only promoted/dismissed, no delete, rumors/ and archive/rumors/, rNNN, cac rumor create flags). skills-authored-only-in-templates is honored, with skills out of scope. cli-mcp-parity and console-best-practices are not triggered. The cited line numbers in branching-guide.md, migration-guide.md and CLAUDE.md match the stale text, AGENTS.md has no rumor references, and the region body does name rumors.py. Notes: (a) the Verification git-diff scope should allow the permitted contradiction fix in workflow.md/tool-reference.md; (b) the 'per campaign' grep will hit the legitimate 'encounters numbered per campaign' in CLAUDE.md, so zero stale hits means after hand review; (c) step 1's clean-tree check should expect the untracked e024 record; (d) the branching guide's collision text lists no record types, so record whether the conditional rumor-number item applies. Unverified and out of surface: docs tests asserting guide strings, and other repo or sourcebook text still describing per-campaign rumors outside the named files.
