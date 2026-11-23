---
archived: false
campaign: c008-sourcebook-integrity
created_by: John Hoff
created_on: '2026-11-23T21:58:29Z'
depends_on: []
kind: scripted
name: e001-open-campaign-goal-adoption
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-11-23T23:31:04Z'
---

## Requirements

Deliver b003's goal-adoption half. A guarded operation adds existing bosses to a campaign after it has left `draft`:

1. **Operation.** Core `coupling.adopt_bosses(root, name, bosses, message)` (wrapped as `campaign.adopt_bosses`) adds bosses to a campaign that is:
   - `open` or `paused`,
   - unarchived,
   - not reactivated.

   Adoption only adds. The existing membership is kept, and the new set is `previous ∪ requested`, ordered by `campaign_bosses.order`.
2. **Eligibility.** Each newly adopted boss passes exactly the draft-selection rule (`coupling._eligible`): `available`, unassigned, every prerequisite satisfied per `boss_candidates.assess`. There is no co-adoption special case.
   - Requested bosses already in the campaign are a no-op for that member.
   - A request where every boss is already a member is read-only: no write and no log entry.
3. **Guards and errors.** Each case below raises before any write, with a message naming the reason:
   - draft campaign (use `campaign_set_bosses` instead),
   - completed or abandoned campaign,
   - archived campaign,
   - reactivated campaign,
   - blank message,
   - empty boss list,
   - duplicate refs after resolution,
   - ineligible boss (names unsatisfied prerequisites, as `_eligible` does),
   - boss owned by another campaign,
   - inconsistent reciprocal links (`Links.current`).
4. **Writes.** On success:
   - Each adopted boss gains `campaign: <name>` and is stamped. Its design is frozen, exactly as with selection; status stays `available`.
   - The campaign's `bosses` list is stored via `campaign_bosses.store`, the campaign is stamped, and a `Log` entry titled `Bosses adopted` is appended with the message plus previous/new membership.
   - All writes run under one `Recovery` cohort with `_minimum_output` checked first, so a failure rolls every record back.
   - The search index stays in sync through the existing `_write_boss` / `write_post` paths.
5. **Reactivated detection.** `campaign.reactivate_campaign` sets a persistent frontmatter flag `reactivated: true`, which is never cleared. Adoption refuses when it is true. An absent flag reads as false, so existing records need no migration. Campaigns reactivated before this change carry only a `Reactivated` log entry. None is currently open, and this limitation is documented rather than inferred from log text.
6. **Surfaces (parity).**
   - MCP `campaign_adopt_bosses(name, bosses, message)` in `mcp/campaign.py`, decorated `@references.inputs("campaign")`, returns `campaign_to_dict` like `campaign_set_bosses`.
   - CLI `cac campaign adopt-bosses NAME --boss REF [--boss REF ...] --message/-m REASON` in `cli/campaign.py`, printing a one-line confirmation with `markup=False`.
   - Both accept short refs (`cNNN`, `bNNN`).
   - Errors surface the core message on both surfaces. The CLI exits non-zero via the existing error handling used by `set-bosses`.
7. **Docs and skills (`workflow-doc-source-of-truth`, `skills-authored-only-in-templates`).** These are template-only edits; the deployed `.claude/skills` and `.agents/skills` copies are untouched, and the developer redeploys.
   - `templates/docs/tool-reference.md`: add an "Adopt into open/paused membership" row and argument row next to set-bosses, with guards, errors and the read-only same-set rule; document the `reactivated` flag on campaigns.
   - `templates/docs/planning-workflow.md` (around lines 222 and 339), `development-workflow.md` (around line 207) and their shared-rule mirrors: replace "adopting ownership of open legacy campaigns is deferred" and "Membership locks once the campaign leaves draft" with the new rule. Draft membership is replaceable with `campaign_set_bosses`. Open or paused, non-reactivated membership can only grow, via `campaign_adopt_bosses`. Reactivated, closed and archived membership is locked.
   - `templates/docs/branching-guide.md` (around line 117) and `migration-guide.md` (around line 328): the same correction where they restate the lock or the deferral.
   - `templates/skills/{claude,codex}/campaign_manager/SKILL.md`: add the operation to the campaign operations table and amend "Membership locks after opening, including reactivation".
   - `templates/skills/{claude,codex}/world_planner/SKILL.md`: amend "Adopting ownership into an already-open legacy campaign is deferred" to point at campaign-manager's adoption operation.
8. `pdm run pytest -q` passes and ruff is clean.

## Rationale

b003 (from r001): c001 opened before its goals existed as bosses, so linking b001/b002 needed a GM-override hand-edit of boss and campaign frontmatter (c001/e025). Membership can only change while a campaign is `draft`, so any goal discovered or recorded mid-campaign has no supported path into an open campaign. The planning decisions recorded on b003 (2026-11-23) fix three choices:
- eligibility is the same as selection;
- adoption is allowed on open/paused campaigns generally, but refused once reactivated, because adding goals during pre-merge review fixes is scope creep;
- reactivated detection is an encounter-level choice.

An explicit `reactivated` flag is chosen over parsing the campaign's `Log` text, because guards elsewhere in core read frontmatter, never body prose.

## Plan

1. **Core (`core/coupling.py`).** Add `adopt_bosses` next to `set_bosses`, mirroring its structure:
   - `campaign_bosses.resolve` the requested refs and reject an empty list.
   - Load via `_campaign` and check status ∈ {open, paused}, not `archived`, not `reactivated`, raising `campaign.CampaignNotMutableError` with specific messages.
   - Check the message.
   - `links = Links(root, campaigns=[name], bosses=names)`; `previous = links.current(name)`; `added = [b for b in names if b not in previous]`; if `added` is empty, return the path (read-only).
   - Call `_eligible(root, added, links)`.
   - For each added boss, set `campaign`, stamp it and collect the change. Then `campaign_bosses.store(post.metadata, previous + added)`, stamp, and `append_log_entry(section="Log", heading="Bosses adopted", message=f"{message}\n\nPrevious bosses: …\nAdopted: …\nNew bosses: …")`.
   - Call `_minimum_output`, then write everything inside `Recovery(root, [path] + targets)`.

   Add `campaign.adopt_bosses` as a thin delegate, as `set_bosses` is.
2. **Reactivated flag (`core/campaign.py`).** In `reactivate_campaign`, set `post["reactivated"] = True` before `_apply_status`. Add the key name to `config.py` if campaign keys live there. Expose `reactivated` in `get_payload` metadata as-is; no other read surface changes.
3. **MCP (`mcp/campaign.py`).** Add `campaign_adopt_bosses` with a docstring stating the guards briefly. The tool-description drift guards in existing tests (if any enumerate campaign tools) are updated.
4. **CLI (`cli/campaign.py`).** Add `adopt-bosses` with `@reference_inputs("campaign")`, a required repeatable `--boss` (list) and a required `--message/-m`. Mirror `set-bosses` for error propagation and output.
5. **Docs and skills.** Make the edits listed in Requirement 7. Keep `planning-workflow.md` and `development-workflow.md` shared-rule text synchronized where both restate it.
6. **Tests (mirroring `src/cac/`).**
   - `tests/core/test_coupling.py` (or `test_campaign_bosses.py`, following where `set_bosses` is tested):
     - Adoption on an open and on a paused campaign: links written both ways, log entry, stamps, status unchanged.
     - Adds to existing members without removing any; a same-set request writes nothing (file bytes unchanged).
     - Every guard in Requirement 3 raises with nothing written. This covers draft, completed, abandoned, archived, reactivated, blank message, empty list, proposed/withdrawn/vanquished boss, unsatisfied prerequisite and a boss owned by another campaign.
     - A failure mid-write rolls back every record (follow the existing `Recovery` test pattern).
     - The adopted boss then completes with the campaign (`campaign_complete` vanquishes it).
   - `tests/core/test_campaign.py`: `reactivate_campaign` sets `reactivated: true`, and the flag survives a later `complete`.
   - `tests/mcp/test_campaign.py` and `tests/cli/test_campaign.py`: the happy path with short refs, the reactivated refusal, and that CLI and MCP produce the same resulting membership and error text.
   - `tests/core/test_docs.py` / skill-template tests: add any registry or drift assertions that already exist for tool tables, so `campaign_adopt_bosses` appears in tool-reference.

## Verification

- `pdm run pytest -q` passes with no skips or deletions, and the new tests cover every Requirement 1–6 case. `pdm run ruff check .` reports zero errors, and `pdm run ruff format .` produces no diffs.
- Manual check in a scratch bootstrapped directory, never this repo's `.sourcebook`:
  - Create two available bosses, create a campaign selecting one, open it, then `pdm run cac campaign adopt-bosses <c> --boss <b2> -m "…"`. Both bosses now show `campaign`, and the campaign log has a `Bosses adopted` entry.
  - Pause the campaign and adopt again with the same set: nothing changes.
  - Reactivate a completed campaign; adoption is refused.
- `grep` over `templates/docs` and `templates/skills` finds no remaining "adoption … deferred" or unconditional "locks once the campaign leaves draft"/"locks after opening" statements.

## Log

### Review - 2026-11-23T23:21:16Z - John Hoff

Independent lore review: PASS-WITH-NOTES. clean-tests-and-lint is honored: pytest and ruff gates are in Req 8 and Verification with no skips or noqa. cli-mcp-parity is honored: CLI adopt-bosses and MCP campaign_adopt_bosses are thin wrappers over core coupling.adopt_bosses, with short refs, shared error text and parity tests. Notes: require the CLI help to agree fact-for-fact with the MCP docstring, which tool-reference must match or exceed; add adopt-bosses to tool-reference's reference-input table (line 161); confirm whether any drift-guard test enumerates campaign tools. console-best-practices is honored (markup=False confirmation). skills-authored-only-in-templates is honored: only templates/skills/{claude,codex} are edited and the developer redeploys. workflow-doc-source-of-truth is honored: tool-reference, the development-workflow primary rule (line 207), the planning mirror (line 339), the planning roadmap deferral (line 222), branching-guide (line 117) and migration-guide (lines 328-329) all change in the same encounter, and the phase guides stay under 40k characters. Notes: name where the limitation for pre-change reactivated campaigns is documented (migration-guide suggested); state the new persistent reactivated flag in development-workflow's reactivation text; Verification's grep misses branching-guide's 'opening locks membership' wording. Internal: Plan step 1 stores previous + added, but Req 1 requires campaign_bosses.order, so reconcile them. Unverified, outside the reviewed surface: duplicate rejection in campaign_bosses.resolve, Links.current raising on inconsistent links, where campaign keys live in config.py, and un-cited restatements of the draft-only lock (e.g. workflow.md).

### Opened - 2026-11-23T23:21:47Z - John Hoff

Developer approved opening after PASS-WITH-NOTES review.

### Message - 2026-11-23T23:26:47Z - John Hoff

Execution notes and deviations:
- Ordering (review internal note): the stored membership is sorted(previous ∪ added) by campaign_bosses.order, which satisfies Req 1. campaign_bosses.resolve already returns adopted refs in canonical order.
- Unverified review points, now confirmed in code: campaign_bosses.resolve/validate rejects duplicates after alias resolution ("Duplicate campaign boss identities."); Links.current raises LinkError on inconsistent reciprocal links; campaign keys live in config.py, so REACTIVATED_KEY was added there; workflow.md does not restate the lock.
- Empty boss list raises campaign_bosses.MembershipError (a ValueError), not a message error.
- The draft-refusal message names both surfaces: "use campaign_set_bosses (CLI: cac campaign set-bosses)".
- Review note 1: the CLI adopt-bosses help and the MCP campaign_adopt_bosses docstring state the same facts, and tool-reference.md is more specific (full guard and error list).
- Review notes 2–3: the tool-reference reference-input table row now covers adopt-bosses; tests/mcp/test_server.py enumerates MCP tools and was updated.
- Review notes 4–5: the pre-change reactivation limitation is documented in migration-guide.md and tool-reference.md. Both phase guides' Reactivation bullets now state the permanent flag.
- Additional mirrors found by grep beyond those cited, and updated: development-workflow.md "opening or reopening locks membership" (branch section) and the migration-guide.md misconceptions table row.
- Out-of-template doc: README.md workflow step 3 said "Membership locks when the campaign opens" and was corrected. The CHANGELOG 0.3.0 entry is historical and left unchanged; no CHANGELOG entry was added, matching c003–c007.
- Manual CLI check done in a scratch directory seeded via the core API (no bootstrap run): adopt on open, read-only all-member request on paused, refusal after reactivation (exit 1).

### Completed - 2026-11-23T23:31:04Z - John Hoff

Verification passed; developer confirmed completion. pytest 1781 passed (no skips or deletions); ruff check/format clean; manual scratch-directory CLI check covered adopt on open, read-only all-member request on paused, and refusal after reactivation; template grep is clean. Skill templates changed, so the developer must redeploy (cac bootstrap init).
