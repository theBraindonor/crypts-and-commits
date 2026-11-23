---
archived: false
campaign: c008-sourcebook-integrity
created_by: John Hoff
created_on: '2026-11-23T23:32:39Z'
depends_on: []
kind: scripted
name: e002-refuse-referenced-deletes
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-11-23T23:55:47Z'
---

## Requirements

Deliver b003's referenced-delete half. `lore_delete`, `region_delete` and `campaign_delete` refuse while the target is referenced, raising before any write. The error lists every referrer so the developer can unassign or remove them first. The referrer set per target is settled here (b003's last open question; developer-confirmed and recorded as ruling c008-e002-…):

1. **Lore** `NAME` is referenced by:
   - the world, when its `assigned_lore` contains `NAME`;
   - every region whose `assigned_lore` contains `NAME`.

   The lore's own `assigned_to_world`/`assigned_regions` fields are not referrers; they are the target's own state.
2. **Region** `NAME` is referenced by:
   - every lore entry whose `assigned_regions` contains `NAME`;
   - every unarchived encounter, in any status and any live campaign, whose `regions` contains `NAME`.

   Encounters under archived campaigns (`archive/encounters/…`) are history and do not block (b003 planning decision).
3. **Campaign** `NAME`:
   - The existing boss guard (`CampaignLinkedError` for current/historical `bosses` membership or a boss claim) is unchanged and still runs first.
   - In addition, the campaign is referenced by every one of its own encounters, live or archived, since they are its children and would be orphaned.
   - It is also referenced by every ruling, live or archived, whose `campaign` metadata names it. Rulings cannot be deleted, so a campaign with rulings is permanently undeletable. This is intended.
4. **Error.** A new `ReferencedRecordError(ValueError)` in a new core module `core/referrers.py`:
   - The message names the target and lists every referrer as `<type> <canonical name> (<field>)`, e.g. `world (assigned_lore)`, `region backend (assigned_lore)`, `lore clean-code (assigned_regions)`, `encounter c001-x/e002-y (regions)`, `ruling c001-e001-z (campaign)`.
   - Referrers are sorted deterministically (by type, then name) and never truncated.
   - It ends with a hint: unassign or remove the referrers first.
5. **No partial effects.** A refused delete leaves every file and the search index byte-identical. An unreferenced target deletes exactly as before.
6. **Parity.**
   - MCP `lore_delete`, `region_delete` and `campaign_delete` raise the core error.
   - CLI `cac lore|region|campaign delete` print the same message via `fail` (`markup=False`) and exit 1. This happens after the existing confirmation prompt, which is unchanged; `--yes` does not bypass the guard.
   - The MCP docstrings and CLI help for the three deletes state the same facts: "refused while referenced; the error lists every referrer".
7. **Docs and skills (`workflow-doc-source-of-truth`, `skills-authored-only-in-templates`).** These are template-only edits; the developer redeploys.
   - `templates/docs/tool-reference.md`: the three delete rows, plus a short "Referenced deletes" paragraph with the referrer table and error format. The campaign-delete paragraph (around line 292) extends the boss guard with encounters and rulings.
   - Phase guides: add or adjust the rule wherever they describe deletion. During execution, grep `planning-workflow.md`/`development-workflow.md` for delete wording and keep the shared rules in sync.
   - `templates/skills/{claude,codex}/world_manager/SKILL.md`: replace "remove an entry, unconditionally" and "remove a region, unconditionally" with the refusal rule.
   - `templates/skills/{claude,codex}/campaign_manager/SKILL.md`: the "Delete permitted bossless draft/history" row and its deletion paragraph mention the new encounter and ruling blockers.
   - Repository `CLAUDE.md` line 84 ("Known limitation: deleting a lore/region/campaign entry does not cascade-clean stale references…") becomes untrue. It is developer-owned, so replacing it with the refusal rule happens only with explicit developer approval at completion; otherwise it is left as-is and the developer is told.
8. `pdm run pytest -q` passes and ruff is clean.

## Rationale

b003 (from r002): deleting lore or regions leaves dangling names in world/region `assigned_lore`, lore `assigned_regions` and encounter `regions`. Applicable-lore resolution and prime read those lists, so a dangling name silently corrupts review context. Deleting a campaign with encounters or rulings orphans them. The developer chose refusal over cascade cleanup, because `campaign_delete` already refuses while bosses are linked. One referrer module keeps the inventory in one place, so later link types are added once.

## Plan

1. **Core `core/referrers.py`** (new, logic only). It uses existing readers: `world.read_metadata`/world path, `region.list_regions` + `read_metadata`, `lore.list_lore` + `read_metadata`, encounter listing over live campaigns (`campaign.list_campaigns`, `encounter.list_encounters` + metadata), archived encounter listing for the target campaign, and `ruling.list_rulings(include_archived=True)` + metadata.
   - `lore_referrers(root, name) -> list[str]`, `region_referrers(root, name)` and `campaign_referrers(root, name)` each return formatted, sorted referrers.
   - `ensure_unreferenced(kind, name, referrers)` raises `ReferencedRecordError`.
   - Missing world or empty directories mean no referrers.
   - Malformed referrer frontmatter surfaces as-is; it is not masked.
2. **Wire into deletes.**
   - `lore.delete_lore` and `region.delete_region` check after `_existing_*_path` and before `delete_post`.
   - `campaign.delete_campaign` checks inside the function body, which runs after the `campaign_operation("delete")` boss guard and before `delete_post`.
   - Import placement avoids cycles; local imports are used where core modules import each other.
3. **Wrappers.**
   - CLI `cli/lore.py`, `cli/region.py` and `cli/campaign.py` delete commands add `ReferencedRecordError` to their caught exceptions and `fail(console, str(exc))`. Help text is updated.
   - MCP `mcp/lore.py`, `mcp/region.py` and `mcp/campaign.py` docstrings are updated and the error propagates as-is.
4. **Docs and skills** as listed in Requirement 7. Grep templates for "unconditionally", "cascade", "dangling" and delete wording, and update every restatement.
5. **Tests (mirroring `src/cac/`).**
   - `tests/core/test_referrers.py`:
     - Each referrer type is detected and formatted.
     - Sorting.
     - Archived-campaign encounters do not block a region delete.
     - A campaign's archived encounters and archived rulings do block.
     - Unrelated names don't match (exact list membership, not substring).
   - `tests/core/test_lore.py`, `test_region.py`, `test_campaign.py`:
     - A refused delete leaves `files()` and index evidence unchanged, and the error lists all referrers.
     - After unassigning, the delete succeeds.
     - Existing unreferenced-delete tests still pass.
     - For campaigns, the boss guard still wins when bosses are linked.
   - `tests/mcp/…` and `tests/cli/…` for lore, region and campaign:
     - The refused delete raises (MCP), or exits 1 with the same message (CLI, with `--yes`).
     - An unreferenced delete still works.

## Verification

- `pdm run pytest -q` passes with no skips or deletions, and the new tests cover Requirements 1–6. `pdm run ruff check .` reports zero errors, and `pdm run ruff format .` produces no diffs.
- Manual check in a scratch directory seeded through the core API (never this repo's `.sourcebook`; no bootstrap run):
  - Assign lore to the world and a region, assign an encounter to the region, then try `cac lore delete X -y` and `cac region delete R -y`. Both are refused, with every referrer listed.
  - Unassign them, then the deletes succeed.
  - `cac campaign delete C -y` on a bossless campaign with an encounter is refused; it succeeds after the encounter is deleted.
- Grep `templates/docs` and `templates/skills` finds no "unconditionally" delete wording for lore or regions.

## Log

### Review - 2026-11-23T23:39:29Z - John Hoff

Independent lore review: PASS-WITH-NOTES. clean-tests-and-lint is honored (Requirement 8 and Verification gate on pytest -q and ruff clean, with no skips or noqa). cli-mcp-parity is honored: no new commands; MCP stays a thin wrapper that propagates ReferencedRecordError; CLI-only confirm/--yes/fail concerns stay in cli/, and --yes cannot bypass the guard; MCP docstrings and CLI help state identical facts, and tool-reference gains a referrer table at least as specific as both. console-best-practices is honored (the error carries stored names and is printed via fail with markup=False). skills-authored-only-in-templates is honored (template-only edits to both world_manager and campaign_manager flavors; the developer redeploys). workflow-doc-source-of-truth is honored with notes: the mirrored campaign-deletion paragraphs (development-workflow ~165, primary; planning-workflow ~298) must change together. Neither phase guide currently describes lore or region deletion, so add the new lore/region guard explicitly in planning-workflow's static-context connections list (~55-70) and its development mirror, rather than relying on 'wherever they describe deletion'. Extend the Verification grep to confirm both campaign_manager flavors name the encounter and ruling blockers. CLAUDE.md:84 is correctly left to developer approval. Unverified and outside the cited surface: the ruling `campaign` field reader, delete behavior on archived campaigns, fail()'s markup handling, and whether any other record type references regions or lore. Consequence to note: a closed campaign with encounters becomes undeletable.

### Opened - 2026-11-23T23:42:15Z - John Hoff

Developer approved opening after PASS-WITH-NOTES review, accepting that closed campaigns with encounters become undeletable.

### Message - 2026-11-23T23:45:54Z - John Hoff

Execution notes and deviations:
- Review-unverified points confirmed in code: rulings store `campaign` in metadata (ruling.read_metadata); archived encounters live under archive/encounters/<campaign> and delete_campaign resolves archived campaigns; no other record type stores lore or region names.
- cli/common.fail() prints through Rich markup (`[bold red]…`) and cannot disable it. To keep stored names literal (Req 6, console-best-practices), I added cli/common.refuse(console, message), which prints with markup=False (bold red style) and exits 1. The three delete commands use it for ReferencedRecordError, and fail() is unchanged elsewhere.
- Campaign encounter referrers render with field `(campaign)` (child relation), e.g. `encounter c001-x/e001-y (campaign)`.
- Ruling referrers are scanned only when world.md exists (ruling.list_rulings requires it). Campaign tests without a world still work.
- Existing test tests/core/test_search_index.py::test_delete_campaign_removes_its_own_row_but_leaves_encounters encoded the old behavior that ruling c008-e002-delete-referrer-set forbids: deleting a campaign with an encounter. It was rewritten, not deleted, as test_delete_campaign_removes_only_its_own_row, keeping its index-scoping intent: the campaign with an encounter is refused with the index unchanged, and an empty campaign's delete removes only its own row.
- Test layout: the core referrer tests and guarded-delete tests are in tests/core/test_referrers.py, with index and file snapshots over *.md (SQLite -wal/-shm files change on read). The CLI/MCP parity tests live together in tests/cli/test_referenced_deletes.py, with one parametrized test comparing the MCP error and CLI output per delete. There are no separate per-module mcp files.
- Docs: tool-reference.md gains a "Referenced deletes" section (referrer table, error format) plus the extended campaign-delete paragraph. Both phase guides gain a mirrored Connections bullet on referenced deletes (review note) and the extended campaign-deletion paragraph, which also states that closed campaigns with encounters, or any campaign with rulings, stay permanently. world_manager (both flavors): lore/region delete lines no longer say "unconditionally". campaign_manager (both flavors): delete row and paragraph name encounter and ruling blockers.
- CLAUDE.md line 84 is pending developer approval at completion.
- Manual scratch check (core-API seeded, no bootstrap): lore, region and campaign deletes are refused with every referrer listed (exit 1), and all three succeed after unassigning/removing referrers.

### Message - 2026-11-23T23:50:22Z - John Hoff

Second existing-test deviation: tests/core/test_index_snapshot.py::test_rebuild_retains_orphan_encounters created its orphan through campaign.delete_campaign, which is now refused. Its intent (an index rebuild tolerates orphan encounters, which older libraries could leave behind) is kept. The test now asserts the supported delete raises ReferencedRecordError, then simulates the legacy orphan by unlinking the campaign file inside its temp directory. Full suite: 1795 passed; ruff clean.

### Completed - 2026-11-23T23:55:47Z - John Hoff

Verification passed; developer confirmed completion and approved replacing CLAUDE.md line 84 with the referenced-delete rule. pytest 1795 passed (no skips; two existing tests rewritten to the new rule with intent preserved, as logged); ruff check/format clean; manual scratch-directory CLI check covered refusals with full referrer lists and success after unassigning; template grep clean. Skill templates changed, so the developer must redeploy (cac bootstrap init).
