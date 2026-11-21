---
archived: false
campaign: c002-rulings
created_by: John Hoff
created_on: '2026-11-21T03:31:41Z'
depends_on:
- e005-ruling-skill-templates
kind: scripted
name: e006-ruling-guides-and-public-docs
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-11-21T03:43:46Z'
---

## Requirements

Finish `b005-ruling-records`'s documentation criterion: "`templates/docs/workflow.md`, `templates/docs/tool-reference.md`, the branching and migration guides, and the packaged skill templates describe the model." The campaign goal also covers this repo's `CLAUDE.md`/`AGENTS.md` domain model and the public docs. `workflow.md` and `tool-reference.md` (e004) and the skill templates (e005) are done. This is the last item in c002's tentative encounter order.

Every statement must match the shipped behavior and `workflow.md`: rulings are named `cNNN-eNNN-slug` (`e000` for campaign-level), captured only in an `open` campaign (reactivated counts), unique across live and archived records, unnumbered with no short refs and no renumber, `recorded` → `canonized`/`noted` with required narratives, reopenable, history-keeping, archived independently of campaigns, never deleted, a `ruling` search type, and every recorded ruling in prime as `recorded_rulings`/`recorded_ruling_count`/`ruling_diagnostics`.

**Packaged guides** (`packages/crypts-and-commits/src/cac/core/templates/docs/`):
- `branching-guide.md`:
  - Branch-roles table: planning triages rulings as well as rumors; an execution branch captures rulings while its campaign is open.
  - Ownership paragraph: campaign-manager captures, world-planner triages (canonize/note/archive) on planning.
  - "Allocate numbers and check conflicts": rulings are not allocated numbers. Their names come from the already-settled campaign and encounter numbers, so cross-branch collisions are not expected and there is no renumber; a duplicate name is refused at create time.
  - Worked path: in the execution step, a worked `ruling_create` / `cac ruling create c012-e003-... --summary ... --origin ... --body-file ...` example for a developer-confirmed choice. In the planning-triage step, list `status="recorded"`, canonize after approved lore/world changes or note, then archive.
  - Archiving a campaign neither moves nor blocks its rulings.
- `migration-guide.md`:
  - "Targeted instruction mapping": a row mapping "decisions scattered across encounter logs/override notes" to "capture developer-confirmed decisions as rulings in the open campaign; triage them on planning".
  - "Version-specific migrations": rulings are additive within schema version 1. `rulings/` and `archive/rulings/` are created lazily; prime gains `recorded_rulings`, `recorded_ruling_count` and `ruling_diagnostics`; the search index gains the `ruling` type, so a developer may be told the index is stale after upgrading and should run `cac index rebuild` themselves. No record migration, schema bump, guardrail suspension or bootstrap migration is needed; adopting the capture/triage procedure needs the developer to redeploy the skills with `cac bootstrap init`.
  - The current schema version line stays 1.

**Repository instructions:**
- `CLAUDE.md`:
  - Guardrail tool lists add `ruling_*` and `cac ruling`.
  - Architecture lists `ruling.py` among the `core/` and `mcp/` modules.
  - "The sourcebook domain model" gains a **`rulings/<name>.md`** bullet, and the numbered-names paragraph says rulings are not numbered and take full names only.
  - "Agent skills": world-planner triages rulings; campaign-manager captures them and records GM overrides as rulings.
  - The opening paragraph's description of the live sourcebook mentions rulings.
- `AGENTS.md`: defers wholesale to `CLAUDE.md` and has no domain model, so it should need no change. Confirm that it doesn't, rather than adding duplicate text.

**Public docs:**
- `README.md`: the skill summary, domain-model list (a **Rulings** bullet), the workflow steps (capture during execution, triage on planning), the MCP tool list and the CLI examples in the dogfooding section.
- `packages/crypts-and-commits/README.md`: the content-type sentence adds **ruling**.
- `docs/QUICKSTART.md`: a short "Record decisions as rulings" section after "Capture ideas as rumors", in that section's style. Create when the developer confirms a choice in an open campaign; triage on planning.
- `docs/CHANGELOG.md`: a new `## [Unreleased]` section above `[0.3.0]` with an "Added" entry for rulings (records, lifecycle, CLI/MCP, search type, prime exposure, skill capture/triage and GM-override capture, docs) and a note that the schema stays at version 1.

**World summary** (sourcebook, through `world_set_body` only): the domain-model list gains a **Ruling** bullet between Rumor and Encounter. The rest of the body is unchanged.

**Tests** (`tests/core/test_docs.py`): one test asserting that `branching-guide` and `migration-guide` each mention `ruling_create`, and that the migration guide states rulings are additive within schema version 1.

## Rationale

`workflow-doc-source-of-truth` makes `workflow.md`/`tool-reference.md` the authority. The other guides and public docs repeat parts of the model, and they must not drift from it now that rulings have shipped. The branching guide matters most: it is where an agent learns which branch does what, and right now it only describes rumor capture and triage.

Rulings are additive storage within schema 1, like boss storage was. The migration guide must say so explicitly, so an agent upgrading a project does not invent a migration or suspend the guardrail. The `ruling` search type is new, so the stale-index note tells the agent to defer to the developer instead of rebuilding.

The world summary is this project's own priming text. Leaving rulings out of its domain model would contradict prime's own `recorded_rulings` field. It is changed only through MCP, per the guardrail.

`CHANGELOG.md` gets an `[Unreleased]` section instead of folding rulings into the dated 0.3.0 Boss Edition entry, because rulings are a separate campaign delivered after that entry. The release number remains the developer's decision.

The new doc test makes the guides' ruling coverage fail CI if it is removed later. It follows the existing per-doc tests in `test_docs.py`.

**Out of scope:**
- Changes to `workflow.md`, `tool-reference.md` or the skill templates, unless the cross-check finds a contradiction; then fix it in the same change and record it in the log.
- Any `src/` code change, version bump or release.
- Triaging the two recorded rulings (`c002-e001-e000-doc-exemption`, `c002-e001-workflow-cap-stopgap`), which belongs to planning.
- Extending the paired-docs leak guard to the branching guide, which uses example campaign numbers on purpose.

## Plan

1. Edit `branching-guide.md` and `migration-guide.md` as listed, keeping their structure and voice. Use only example names (`c012-...`), never this repo's campaign/encounter names.
2. Add the doc test to `tests/core/test_docs.py`.
3. Edit `CLAUDE.md`, `README.md`, `packages/crypts-and-commits/README.md`, `docs/QUICKSTART.md` and `docs/CHANGELOG.md` as listed. Re-read `AGENTS.md` and confirm it needs no change.
4. Update the world summary's domain model with `world_set_body`. Read the current body with `world_get` first, and change only the domain-model list.
5. Cross-check every new ruling statement against `workflow.md` (Rulings domain section, Capture rulings, Planning handoff) and `tool-reference.md` (ruling tool contracts, prime and search). Fix any contradiction at its source.
6. Run the full suite and ruff.

## Verification

- `pdm run pytest -q` passes, including the new doc test and the existing `test_docs.py` budget tests for both guides. No skips or deletions.
- After applying `pdm run ruff format .`, `pdm run ruff check .` and `pdm run ruff format --check .` are clean.
- `grep -ci ruling` is non-zero for `branching-guide.md`, `migration-guide.md`, `CLAUDE.md`, `README.md`, `packages/crypts-and-commits/README.md`, `docs/QUICKSTART.md` and `docs/CHANGELOG.md`. `AGENTS.md` is unchanged, with a stated reason.
- `world_get` shows the Ruling bullet in the domain model and otherwise the same body.
- The step 5 cross-check found no contradictions with `workflow.md`, `tool-reference.md` or shipped behavior. Any fixes made are listed in the completion message.
- This repo's deployed `.claude/skills/` and `.agents/skills/` were not edited by this encounter.

## Log

### Review - 2026-11-21T03:34:15Z - John Hoff

PASS-WITH-NOTES: The applicable lore is clean-tests-and-lint, cli-mcp-parity, console-best-practices, skills-authored-only-in-templates and workflow-doc-source-of-truth. This is a docs-only encounter with no `src/` change, so cli-mcp-parity and console-best-practices do not apply. Verification enforces the full pytest suite (including the existing `test_docs.py` budget tests) and clean ruff check/format. The deployed skill copies are explicitly left untouched, with bootstrap left to the developer. The Plan treats `workflow.md`/`tool-reference.md` as the authority, cross-checks every new ruling statement against them, and fixes any contradiction at its source in the same change. Its stated model (`cNNN-eNNN-slug`, `e000`, open-campaign capture including reactivated campaigns, uniqueness across live and archived records, no numbering, short refs or renumber, canonize/note with a resolution, reopen, independent archive, no delete, the `ruling` search type, and the prime fields) matches both docs. The world summary is changed only through `world_get`/`world_set_body`, and the stale-index note defers rebuilding to the developer. Notes: (1) state the nonzero-`eNNN`-must-exist guard wherever the open-campaign guard appears, and keep "until triaged" when describing prime's `recorded_rulings`; (2) the `crypts-and-commits` region text still lists the `core/` modules without `ruling.py`, so update it or capture it as a rumor; (3) keep the already-modified deployed skill files out of this encounter's commit so the claim that it did not edit them stays true.

### Opened - 2026-11-21T03:36:12Z - John Hoff

Opened with developer approval. Implementation will fold in reviewer notes 1 and 3. The region-text note (2) is pending a developer decision: update in e006 with an approved summary, or capture as a rumor.

### Message - 2026-11-21T03:41:51Z - John Hoff

Implementation complete, pending developer confirmation.

- **branching-guide.md:**
  - The roles table and ownership paragraph now cover ruling capture (execution branch, open campaign) and triage (planning).
  - A new paragraph in "Allocate numbers" explains why rulings have no numbers, short refs or renumbering, and that duplicate names are refused.
  - Step 5 adds a worked `ruling_create` example with the open-campaign and existing-encounter guard (reviewer note 1).
  - Step 7 adds triage (`status="recorded"`, "until triaged", canonize after approved changes or note, archive) and states that campaign archiving never touches rulings.
- **migration-guide.md:** a new instruction-mapping row; the shared-guidance sample mentions ruling triage; a "Rulings are additive within schema version 1" paragraph covers lazy storage, the new prime fields, the stale `ruling` index (rebuilt by the developer) and skill redeployment. The schema line stays 1.
- **test_docs.py:** `test_supporting_guides_describe_rulings`, parametrized over both guides.
- **CLAUDE.md:** the purpose paragraph, tool lists, the `core/` and `mcp/` module lists, a `rulings/<name>.md` domain bullet (with both create guards), a full-name-only note and the skill roles.
- **README.md:** skills, a Rulings domain bullet, short refs, workflow steps 5 and 7, sourcebook mentions, a `cac ruling list` example and `ruling_list`.
- **Package README:** **ruling** in the content sentence.
- **QUICKSTART.md:** a new "Record decisions as rulings" section; its CLI flags were checked against `--help`.
- **CHANGELOG.md:** a new `[Unreleased]` section.
- **World summary:** a Ruling bullet added through `world_set_body`; the rest of the body is unchanged.
- **AGENTS.md:** unchanged. It imports `CLAUDE.md` wholesale and has no domain model of its own, and the migration guide says to keep shared guidance in `CLAUDE.md` when AGENTS imports it.

**Cross-check (Plan step 5):** every new statement was checked against `workflow.md` (Rulings, Numbering, Capture rulings, Planning handoff) and `tool-reference.md` (Rulings create guards, prime `recorded_rulings`, index staleness). No contradictions were found, and the authoritative docs and templates were not changed.

**Verification:**
- pytest: 1698 passed.
- ruff format and check clean.
- `grep -ci ruling` is non-zero in all seven target files.
- The deployed `.claude/skills` and `.agents/skills` files were already modified before this encounter (the developer's e005 redeploy) and were not touched here. They must stay out of e006's commit (reviewer note 3).

**Pending:** reviewer note 2. The region body's `core/` module list lacks `ruling.py`; the developer has not yet decided whether to update it here or capture a rumor.

### Completed - 2026-11-21T03:43:46Z - John Hoff

Completed with developer confirmation. Verification passed:
- 1698 tests passed, including the new `test_supporting_guides_describe_rulings`.
- ruff format and check clean.
- `ruling` appears in all seven target docs; `AGENTS.md` was left unchanged on purpose, because it imports `CLAUDE.md`.
- The world summary gained only a Ruling bullet.
- Cross-checking against `workflow.md` and `tool-reference.md` found no contradictions.

Reviewer note 2 was resolved by developer choice (a). The `crypts-and-commits` region body now lists `ruling.py` among the `core/` modules, its summary unchanged, recorded as ruling `c002-e006-region-text-in-scope`. The deployed skill copies were not touched by this encounter and belong in a separate commit.
