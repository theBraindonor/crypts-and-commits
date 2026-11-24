---
archived: false
bosses: []
created_by: John Hoff
created_on: '2026-11-24T02:04:13Z'
name: c009-release-0-4-0-docs
status: completed
updated_by: John Hoff
updated_on: '2026-11-24T02:14:18Z'
---

# c009 - Release 0.4.0 documentation

Bossless release-readiness campaign. A pre-release review of `v0.3.0..HEAD` (campaigns c002-c008; tests and ruff clean, deployed skills in sync with templates) found the code ready but the release-facing documentation incomplete or stale. This campaign fixes the documentation only; no `cac` behavior changes.

## Goals

1. **Changelog** (`docs/CHANGELOG.md`): turn `[Unreleased]` into a complete `[0.4.0] - <date>` entry covering every campaign since 0.3.0, not just c002:
   - c002 rulings (existing text; fix the stale "Workflow Reference Guide" bullet).
   - c003 workflow guide split: `planning-workflow` and `development-workflow` registered; `workflow` becomes a short routing index (behavior change for `docs_get("workflow")` consumers).
   - c004/c005 tool and CLI description accuracy; MCP descriptions registered cleaned (`CleanDescriptionServer`).
   - c006 `prime_applicable_lore` paged over MCP: result changes from a bare list to `{items, next_cursor}` plus `cursor` (breaking for MCP consumers); demo-api literal system-message priming fix.
   - c007 plain list pages measured as compact JSON (page boundaries move; CLI and MCP break identically).
   - c008 `campaign_adopt_bosses` / `cac campaign adopt-bosses` with the persistent `reactivated` flag; referenced lore/region/campaign deletes refused with every referrer listed (behavior change).
   - Remove the stale "The release number has not been chosen yet." sentence from `[0.3.0]`.
2. **Migration guide** (`templates/docs/migration-guide.md`, "Upgrading from 0.3.0 to 0.4.0"): add the missing consumer-visible changes - refused referenced deletes, JSON-measured plain-list page boundaries, `workflow` doc now a routing index, and open-campaign boss adoption (summarize or cross-reference the existing note under "Adopt an existing roadmap", including the pre-0.4.0 reactivated-campaign caveat).
3. **Stale membership statements**: `CLAUDE.md` campaign bullet ("editable only while `draft`") and `docs/QUICKSTART.md` (~line 346, "membership locks when the campaign opens") must reflect that open or paused, never-reactivated campaigns can adopt more bosses.
4. **Cleanup**: delete the c003 working notes `docs/workflow-guide-split-design.md` and `docs/workflow-context-update-proposal.md` (developer decision: delete to keep things clean), and fix any links to them.

## Constraints

- Packaged docs follow `workflow-doc-source-of-truth`; keep any shared rules synchronized with their owning guide.
- Skill templates are not expected to change; if one must, edit only `templates/skills/**` and the developer redeploys.
- `clean-tests-and-lint` gates every encounter (doc tests such as `test_docs`/`test_templates` must still pass).

## Success

All four goals done, `pdm run pytest -q` and ruff clean, and the changelog and migration guide accurately describe everything shipping in 0.4.0.

## Log

### Completed - 2026-11-24T02:14:18Z - John Hoff

Postmortem: the 0.4.0 release documentation is complete, done in a single encounter (e001). A pre-release review of v0.3.0..HEAD found the code ready but the docs behind it. The changelog covered only c002, the migration guide was missing four changes users would notice, CLAUDE.md and QUICKSTART still said boss membership locks when a campaign opens, and two c003 working notes had gone stale. e001 wrote the [0.4.0] - 2026-11-23 changelog entry, added the missing migration notes, fixed the membership wording, and deleted the working notes (ruling c009-e000-delete-c003-working-notes). Every claim was checked against the code first. The independent review passed with notes, and all of its notes were addressed. Tests (1795) and ruff are clean. The campaign had no boss, so no goals were vanquished. Follow-up on planning: triage the c009 ruling and archive the campaign.
