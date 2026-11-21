---
archived: false
campaign: c002-rulings
created_by: John Hoff
created_on: '2026-11-21T03:05:56Z'
depends_on:
- e004-ruling-workflow-procedure
kind: scripted
name: e005-ruling-skill-templates
regions:
- crypts-and-commits
status: reviewed
updated_by: John Hoff
updated_on: '2026-11-21T03:09:11Z'
---

## Requirements

Bring the packaged skill templates, in both provider flavors, into line with the ruling procedure in the Workflow Reference Guide, per `b005-ruling-records`'s success criterion: "world-planner triages rulings alongside rumors, including the procedure for canonizing a ruling into lore. campaign-manager, and any skill working in an open campaign, captures a ruling when the developer confirms an answer to an open question or choice, including the reason for a REJECT override."

The files are:
- `templates/skills/claude/campaign_manager/SKILL.md`
- `templates/skills/codex/campaign_manager/SKILL.md`
- `templates/skills/claude/world_planner/SKILL.md`
- `templates/skills/codex/world_planner/SKILL.md`
- `templates/skills/claude/world_manager/SKILL.md`
- `templates/skills/codex/world_manager/SKILL.md`

The Claude flavor uses `mcp__crypts-and-commits__`-prefixed tool names; the Codex flavor uses bare names, as each already does. Each pair stays functionally equivalent, with wording in each file's own style.

**campaign-manager (both flavors):**
1. **Capture rulings.** A paragraph next to the existing rumor-capture guidance in "Discoveries and unusual handoffs":
   - **When:** when the developer confirms an answer to an open question or choice in the open campaign (a boss or encounter open question, a plan choice, or the reason for a REJECT override), record it in the same exchange.
   - **How:** `ruling_create(name,body,summary,origin)` / `cac ruling create NAME --summary TEXT --origin TEXT --body-file PATH`.
   - **Name:** `cNNN-eNNN-slug` for the open campaign and current encounter (`e000` when none). The slug must be unused across every `ruling_list(include_archived=True)` page. Rulings are not numbered and take full names only.
   - **Content:** record only what the developer confirmed, with the developer as origin. Never ask whether it matters enough. Edit only while `recorded`, with `ruling_update`.
   - **Limits:** a ruling never replaces the encounter log or rumors. With no open campaign, capture a rumor. Triage belongs to world-planner.
2. **GM override.** In the REJECT/NOT-REVIEWABLE paragraph of "Encounter Lifecycle":
   - On REJECT only, the agent may offer an explicit GM override and never grants one itself.
   - If the developer overrides with a stated reason, that is the draft→reviewed authorization. Run `encounter_review` with the reviewer's findings verbatim, followed by the override and its reason. Then capture the reason as a ruling.
   - NOT-REVIEWABLE has no override.
   - Gate 2 (separate approval to open) still applies.
   - The gate text stays stop-and-ask in the file's own words, as "Explicit user gates" requires of both campaign-manager templates.
3. **Codex only:** the post-review report guidance ("For REJECT or NOT-REVIEWABLE, keep the encounter draft…") gains the override path: transition first with the override message, report, then ask separately to open.
4. **Orientation:** prime's `recorded_rulings` (with `recorded_ruling_count` and `ruling_diagnostics`) shows untriaged decisions. Respect them during execution, and hydrate with `ruling_get` when relevant.

**world-planner (both flavors):**
1. **Orientation:** prime's line about active bosses also names `recorded_rulings`, `recorded_ruling_count` and `ruling_diagnostics`.
2. **Ruling triage.** A paragraph in "Rumors, archival, and handoff":
   - On synchronized planning, triage integrated recorded rulings with the developer. Page `ruling_list(status="recorded")` / `cac ruling list --status recorded`, read with `ruling_get` / `cac ruling get NAME`, and search with `index_search(phrase,object_type="ruling")`.
   - **Canonize:** after making the lore, region or world changes the developer approves (through world-manager's tools, with its summary-approval rule), run `ruling_canonize(name,message)` / `cac ruling canonize NAME --message TEXT`, with a narrative of what changed.
   - **Note:** otherwise `ruling_note(name,message)` with a narrative of why no change is needed. A superseded ruling is noted with a narrative naming its successor.
   - **Reopen:** `ruling_reopen(name,message)` undoes either.
   - **Archive:** archive every dispositioned ruling with `ruling_archive(name)` / `cac ruling archive NAME`. There is no delete, no renumber and no formal lore link.
   - **Planning decisions:** decisions made during planning itself, with no open campaign, are not rulings. They go straight into goal notes or lore with the developer.
3. **Frontmatter:** the `description` adds ruling triage to rumor triage.

**world-manager (both flavors):**
1. **Prime description:** the `prime_get` bullet and disclosure-ladder step 1 add the recorded rulings as summary-only routing entries, hydrated with `ruling_get`, plus the exact count and diagnostics.
2. **Capture pointer:** one sentence. When the developer confirms a world, lore or region decision while a campaign is open, capture it as a ruling, following campaign-manager's capture rules and the workflow guide's "Capture rulings".

**Tests:** `tests/core/test_skills.py`:
- Add `ruling` to the call-name pattern in `test_packaged_skill_metadata_and_callable_examples_match_interfaces`, so every `ruling_*(` call in a template must name a registered tool.
- Add one content test:
  - both campaign-manager flavors mention `ruling_create` and the GM override;
  - both world-planner flavors mention `ruling_canonize`, `ruling_note` and `ruling_archive`;
  - both world-manager flavors mention `recorded_rulings`.

**Docs:** `workflow.md` already owns this procedure (e004). The skill changes must not contradict it, and any inaccuracy found is fixed in the same change. `tool-reference.md` needs no change, because no tool contract changes.

## Rationale

`skills-authored-only-in-templates` makes the packaged templates the only source of skill text. `workflow-doc-source-of-truth` requires a skill procedure change to be reflected in `workflow.md` in the same change; e004 already authored that procedure, so this encounter implements it in the templates and checks the two against each other.

"Explicit user gates" requires both campaign-manager templates to state each gate's stop-and-ask in their own words, so the override path must appear in both, not only as a cross-reference.

Capture stays skill guidance, not core enforcement (b005).

Extending the call-name pattern makes the existing interface test cover ruling tool references, so a misspelled ruling tool fails CI.

This repository's deployed copies under `.claude/skills/` and `.agents/skills/` are not edited. The developer redeploys them with `cac bootstrap init` when they choose. Until then, this session's deployed skills remain the older text.

**Out of scope:**
- The branching guide, migration guide, `CLAUDE.md`/`AGENTS.md` and public docs (final c002 encounter).
- Any code change in `src/`.

## Plan

1. Edit the six templates as listed in Requirements, keeping the existing structure, tone and per-flavor tool-name conventions, and leaving unrelated text intact.
2. Update `tests/core/test_skills.py`: add `ruling` to the call regex, and add the content test.
3. Read each edited template section side by side with `workflow.md` (Ownership, Allocate numbers, Capture rulings, Review flow and Explicit user gates, Codex encounter handoffs, Planning handoff, and the Rulings domain section). Confirm there are no contradictions and that each claim matches shipped tool behavior.
4. Run the full suite and ruff.

## Verification

- `pdm run pytest -q` passes, including the extended `test_skills.py` interface test (every `ruling_*(` call and `cac ruling …` example resolves to a real tool or command) and the new content test. No skips or deletions are added to dodge failures.
- `pdm run ruff format .` has been applied, and then `pdm run ruff check .` and `pdm run ruff format --check .` are clean.
- In a temporary scratch directory, call `skills.deploy_skills` from core Python, never `cac bootstrap init`. Confirm the six deployed files contain the new ruling guidance, and that this repository's `.claude/skills/` and `.agents/skills/` are untouched (clean `git status` for those paths).
- A side-by-side reading confirms:
  - both campaign-manager flavors state the override path inside the gate procedure and keep every gate's stop-and-ask;
  - the Claude and Codex flavors of each skill are functionally equivalent;
  - nothing contradicts `workflow.md` or the shipped `ruling_*` tools.

## Log

### Review - 2026-11-21T03:09:11Z - John Hoff

PASS-WITH-NOTES. Independent review against clean-tests-and-lint, skills-authored-only-in-templates, workflow-doc-source-of-truth, cli-mcp-parity and console-best-practices. The Plan edits only the six packaged templates under templates/skills/{claude,codex}/ and leaves the deployed .claude/skills and .agents/skills copies untouched. Its deploy check uses core skills.deploy_skills in a scratch directory, never cac bootstrap init. Verification gates on a full pytest pass with no skips or deletions and on clean ruff check and format. workflow.md already owns the ruling procedure (e004), and the Plan checks the templates against it side by side, fixing any inaccuracy in the same change. Leaving tool-reference.md unchanged is justified because no contract changes. Spot checks found the specified guidance consistent with workflow.md and tool-reference.md: the cNNN-eNNN-slug naming with e000, capture in the same exchange, a rumor when no campaign is open, an override on REJECT only that the agent never grants and that is recorded as findings verbatim plus reason and captured as a ruling, no override for NOT-REVIEWABLE, gate 2 preserved, Codex transition-then-report-then-ask, canonize/note/reopen/archive with narratives and no delete, and the prime fields recorded_rulings, recorded_ruling_count and ruling_diagnostics. The tool signatures match the shipped ruling_* contracts, and the Claude allowed-tools already grant the whole server. cli-mcp-parity and console-best-practices do not apply. Notes: (1) at completion, explicitly ask the developer to run cac bootstrap init to redeploy; (2) make sure no other prime description in the templates (for example campaign-manager orientation or world-manager's wider ladder) goes stale; (3) pin the GM-override content assertion to specific wording rather than a loose phrase; (4) confirm the embedded reviewer prompt needs no change. Flagged but unverified: prime mentions outside the named sections, and whether world-manager's frontmatter description should mention rulings.
