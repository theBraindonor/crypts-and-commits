---
archived: false
campaign: c009-release-0-4-0-docs
created_by: John Hoff
created_on: '2026-11-24T02:06:32Z'
depends_on: []
kind: scripted
name: e001-release-0-4-0-docs
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-11-24T02:13:09Z'
---

# Requirements

Bring all release-facing documentation in line with what ships in 0.4.0 (`v0.3.0..HEAD`: campaigns c002-c008). Documentation only; no `cac` source, test-logic or skill-template changes.

1. `docs/CHANGELOG.md`
   - Rename `## [Unreleased]` to `## [0.4.0] - <YYYY-MM-DD>`. The developer confirms the release date during execution; it defaults to the day the encounter completes.
   - Rewrite the intro so it no longer says everything came from `c002-rulings`. It should say the release is the result of campaigns c002-c008 and that the sourcebook schema stays at version 1 with no record migration or bootstrap rerun required.
   - Keep the existing rulings bullets. Replace the stale "Docs: rulings in the Workflow Reference Guide, ..." bullet with the current guide names (planning and development workflow guides, Tool Reference, Branching Guide, Migration Guide).
   - Add entries, grouped under `### Added` / `### Changed`:
     - c003: `planning-workflow` and `development-workflow` guides registered with `docs_get` / `cac docs get`. `workflow` becomes a short routing index; it used to be the full domain-model reference.
     - c004/c005: MCP tool and CLI help descriptions corrected for accuracy, including every searchable index type and ruling-aware text. MCP tool descriptions are registered with docstring indentation cleaned.
     - c006: **Breaking for MCP consumers.** `prime_applicable_lore` is paged. It takes an optional `cursor` and returns `{items, next_cursor}` instead of a bare list. `cac prime applicable-lore` pages at the same boundaries. The demo-api priming fix: the persona and sourcebook priming are passed as literal system messages, so braces in priming text are no longer read as template variables.
     - c007: plain list pages (`lore_list`, `region_list` and the other name lists that share this paging) are measured as the compact JSON MCP returns. Page boundaries may move, and the CLI and MCP break at the same items.
     - c008: `campaign_adopt_bosses` / `cac campaign adopt-bosses` add eligible bosses to an open or paused campaign that was never reactivated. Reactivation now records a persistent `reactivated` flag that locks membership. `lore_delete`, `region_delete` and `campaign_delete` (and their CLI commands) are now refused while another record still references the target, and the error lists every referrer.
   - In `## [0.3.0]`, delete the sentence "The release number has not been chosen yet."
   - Before writing each c004-c008 entry, check its precise claims (exact list tools covered by c007, exact referrer set for c008) against the code and `templates/docs/tool-reference.md`. The changelog must not overstate.
2. `packages/crypts-and-commits/src/cac/core/templates/docs/migration-guide.md`, subsection "Upgrading from 0.3.0 to 0.4.0". Keep the existing rulings and applicable-lore paragraphs verbatim, including the sentence "Rulings are additive within schema version 1.", which `tests/core/test_docs.py` asserts. Add short paragraphs for:
   - Refused referenced deletes: what now fails, that the error lists every referrer, and that the fix is to unassign/remove the references first. No record migration is needed.
   - JSON-measured plain-list paging: page boundaries may change; consumers must follow `next_cursor` and not assume page sizes.
   - The workflow guide split: `docs_get("workflow")` now returns a routing index. Consumers and local agent instructions that cited it as the full reference should use `planning-workflow` / `development-workflow`. Adopting this is a skill or instruction change, so the developer redeploys with `cac bootstrap init`, as described above.
   - Open-campaign boss adoption: one or two sentences plus a cross-reference to the existing note under "Adopt an existing roadmap". Do not duplicate that note, but restate the caveat that campaigns reactivated by a pre-0.4.0 library carry no `reactivated` flag and must not have goals adopted into them.
3. `CLAUDE.md`, campaign bullet in "The sourcebook domain model": replace "editable only while `draft`" with wording that says draft membership can be replaced, and that open or paused campaigns that were never reactivated can only add (adopt) bosses. Reactivated, closed and archived membership is locked. The bullet stays one line.
4. `docs/QUICKSTART.md` (~line 346): replace "membership locks when the campaign opens" with the same rule: select before opening, after which the campaign can only adopt more ready bosses while open or paused and never reactivated. Use `cac campaign adopt-bosses` as the CLI name.
5. Delete `docs/workflow-guide-split-design.md` and `docs/workflow-context-update-proposal.md`, per ruling `c009-e000-delete-c003-working-notes`. Confirm nothing outside `.sourcebook/` links to them; sourcebook history that mentions them stays as is.

# Rationale

The pre-release review found the code ready (tests and ruff clean, deployed skills in sync with templates), but the changelog describes only c002, the migration guide omits four consumer-visible changes, two documents still describe the pre-c008 "membership locks on open" rule, and two c003 working notes are stale. Release notes that understate breaking changes (the shape of `prime_applicable_lore`'s result, refused deletes) would mislead upgraders. One encounter is enough, because every change is a small documentation edit made against the same review findings.

Under `workflow-doc-source-of-truth`, migration-guide owns upgrade instructions. The phase guides and tool-reference already describe adoption, referenced deletes and paging (confirmed during the review), so no phase-guide, tool-reference or skill-template change is expected. If execution finds a mismatch there, record it as an encounter message and fix every affected mirror in the same change.

# Plan

1. Re-read the code and tool-reference sections for c006-c008 (`core/budget.py::json_page` callers, `core/referrers.py`, `core/coupling.py::adopt_bosses`, tool-reference "Referenced deletes" and the list paging text) to pin down the exact claims.
2. Edit `docs/CHANGELOG.md` per Requirement 1.
3. Edit the migration guide per Requirement 2, keeping the asserted sentence and avoiding the forbidden phrases checked by `test_guides_never_narrow_canonize_to_lore` ("rulings into lore", "name no lore records").
4. Edit `CLAUDE.md` and `docs/QUICKSTART.md` per Requirements 3 and 4.
5. `git rm` the two c003 working notes. Grep the repo (excluding `.sourcebook/`, `.venv`, `.nox`, `htmlcov`) for their filenames to confirm there are no remaining links.
6. Grep the non-sourcebook docs again for stale phrasing: "membership locks", "editable only while", "Workflow Reference Guide", "release number has not been chosen".

# Verification

- `pdm run pytest -q` passes with no skips added. Doc tests (`tests/core/test_docs.py`, `tests/cli/test_docs.py`, `tests/mcp/test_docs.py`) cover the migration guide.
- `pdm run ruff check .` reports zero errors and `pdm run ruff format --check .` reports no changes.
- The stale-phrase grep from Plan step 6 returns no hits outside `.sourcebook/` and the changelog's historical `[0.3.0]` text, where describing the then-current rule is accurate.
- `pdm run cac docs get migration-guide` shows the expanded 0.3.0 to 0.4.0 subsection.
- `git diff --stat` touches only `docs/CHANGELOG.md`, `docs/QUICKSTART.md`, `CLAUDE.md`, `templates/docs/migration-guide.md`, the two deleted files and the c009 sourcebook records.
- The developer reviews the final changelog and migration text and confirms the release date before completion.

## Log

### Review - 2026-11-24T02:08:38Z - John Hoff

Independent lore review: PASS-WITH-NOTES. clean-tests-and-lint is honored (pytest, ruff check and a format check in Verification; apply format fixes rather than only reporting them). cli-mcp-parity and console-best-practices are not triggered: docs only, no CLI/MCP command, description or console changes. skills-authored-only-in-templates is honored: no skill-template or deployed-skill edits, and the developer redeploys via `cac bootstrap init`. workflow-doc-source-of-truth is honored: upgrade instructions go to the owning migration-guide, the asserted 'Rulings are additive within schema version 1.' sentence is kept and the forbidden phrases are avoided, and the Rationale justifies leaving the phase guides and tool-reference untouched and commits to fixing every mirror if a mismatch is found. The cited claims match tool-reference (adopt-bosses, reactivated flag, Referenced deletes table). Notes: (1) the c007 entry must list exactly the `json_page`-paged lists (lore, region, docs, prime); (2) word the c003 entry as the phase split so it doesn't read as the [0.3.0] workflow→tool-reference split listed again; (3) exclude `.ruff_cache` from the link grep. Flagged, not verified: README files and AGENTS.md may carry stale membership or workflow wording, and the package version bump for 0.4.0 is not addressed.

### Opened - 2026-11-24T02:09:18Z - John Hoff

Developer approved opening.

### Message - 2026-11-24T02:12:36Z - John Hoff

Execution notes.
- Claims checked against the code. The callers of `json_page` are lore_list, region_list and docs_list (c007) plus prime_applicable_lore (c006), so the c007 changelog entry and the migration paragraph name exactly lore_list, region_list and docs_list. The referrer set matches the tool-reference "Referenced deletes" table.
- The c003 entry is worded as the phase-guide split, and the `workflow` routing index is described separately, so it doesn't repeat the [0.3.0] workflow→tool-reference split (reviewer note 2).
- The link check for the deleted notes left out `.ruff_cache` (reviewer note 3).
- Checks on the reviewer's flagged items: AGENTS.md has no stale membership wording and doesn't treat workflow as the full reference; the root README, package README and QUICKSTART already call `workflow` a task router. The 0.4.0 version bump was already in all pyproject files. Nothing extra needed editing.
- The only stale-phrase hits left are historical [0.3.0]/[0.2.0] changelog lines that were accurate for those releases.
- The changelog date is set to 2026-11-23 for now; the developer confirms it.
Verification: pytest 1795 passed; `ruff format .` left 363 files unchanged; `ruff check` passed; `cac docs get migration-guide` shows the four new paragraphs. Staged diff: CLAUDE.md, docs/CHANGELOG.md, docs/QUICKSTART.md, migration-guide.md, plus the two deleted notes and the c009 sourcebook records.

### Completed - 2026-11-24T02:13:09Z - John Hoff

Verification passed (pytest 1795 passed, ruff format/check clean, migration-guide renders the new 0.4.0 notes, diff limited to the planned files). Developer reviewed the changes and confirmed the 0.4.0 release date of 2026-11-23.
