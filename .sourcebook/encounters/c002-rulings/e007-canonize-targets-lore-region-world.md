---
archived: false
campaign: c002-rulings
created_by: John Hoff
created_on: '2026-11-21T03:47:07Z'
depends_on:
- e006-ruling-guides-and-public-docs
kind: scripted
name: e007-canonize-targets-lore-region-world
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-11-21T03:57:20Z'
---

## Requirements

The developer has confirmed that canonizing a ruling can target any part of the world, not only lore: **ruling → (lore | region | world)**. A canonized ruling's narrative records whichever lore entries, region records (body, summary, path or assigned lore) or world summary/settings were updated. Core, the CLI/MCP contracts, `workflow.md`'s Rulings and Planning handoff sections, `tool-reference.md` and the world-planner procedure paragraphs already say this. Some prose still narrows it to lore and must be brought into line, with no change to behavior.

Change these lore-only phrasings to cover lore, region and world:

**Packaged templates** (`packages/crypts-and-commits/src/cac/core/templates/`):
- `skills/claude/world_planner/SKILL.md` and `skills/codex/world_planner/SKILL.md` frontmatter `description`: "triage recorded rulings into lore" becomes triage into lore, region or world updates. Keep both flavors identical in wording.
- `docs/workflow.md` Rulings section: "Rulings name no lore records" becomes "Rulings name no lore, region or world records" (no formal links of any kind). This stays within the 45,000-character cap in `test_docs.py`.
- `docs/branching-guide.md` worked-path step 7: "If the developer wants standing lore" becomes a lore/region/world-neutral condition.
- `docs/migration-guide.md` instruction-mapping row: "approved lore/world changes" becomes "approved lore, region or world changes".

**Repository instructions and public docs:**
- `CLAUDE.md`: the `rulings/<name>.md` bullet's "Rulings name no lore records" gets the same expansion; check the world-planner skill bullet's "lore/world" wording and add region.
- `README.md`: the Rulings domain bullet ("into the world's lore or noting why it needs none") and workflow step 7 ("should become lore").
- `packages/crypts-and-commits/README.md`: "canonized into lore" becomes canonized into lore, region or world updates.
- `docs/QUICKSTART.md`: "the reason it needs no lore" becomes the reason no world change is needed. Add one region-targeted canonize example alongside the lore example.
- `docs/CHANGELOG.md` `[Unreleased]`: the intro's "standing lore" and the Skills entry's "lore/world changes" include region.

**Sourcebook (MCP only):**
- World summary Ruling bullet (`world_set_body`): "narrative of the lore/world changes made" becomes "lore, region or world changes made". The rest of the body is unchanged.
- c002 campaign body (`campaign_update`, allowed while open): the Goals bullets "canonized into the world's lore" and "its canonize procedure creates or updates lore" are expanded the same way. Membership and the Log are untouched.
- `b005-ruling-records` is **not** edited. Its design is frozen now that it is assigned, and its body already describes canonizing as "how the world (lore, regions, world summary) was updated". The developer's ruling records the decision so the summary's narrower wording is not read as the rule.

**Tests:**
- Extend the world-planner content assertions in `tests/core/test_skills.py` so both flavors' descriptions mention region and world for ruling triage.
- Add a regression check in `tests/core/test_docs.py` that no registered guide contains the phrases "rulings into lore" or "name no lore records".

## Rationale

The developer's intent is that planning can turn a ruling into whichever standing context fits: a convention (lore), a path's documentation (region), or the project summary or branch settings (world). Several decisions in this campaign were region or world changes (e006's region module list and world domain model). A lore-only description would push planners to invent lore for them, or to note them when they should be canonized.

The skill `description` matters most, because it drives when the skill triggers and how an agent frames triage. `skills-authored-only-in-templates` keeps that change in the packaged templates. `workflow-doc-source-of-truth` requires the authoritative docs to agree; `workflow.md` needs only the one sentence about links, and `tool-reference.md` needs nothing.

No code change is needed: canonize already takes a free-text narrative and never inspects or links lore. Adding formal ruling-to-region or ruling-to-world links would contradict b005's "narrative dispositions instead of formal lore links", which this change keeps.

**Out of scope:**
- Any `src/` Python change, including tool docstrings, which already say lore/regions/world.
- Editing b005.
- Test fixture narratives such as "Added lore", which are illustrative.
- Triaging any recorded ruling.
- Redeploying the skills (developer-run `cac bootstrap init`).

## Plan

1. Edit the two world-planner descriptions, `workflow.md`, `branching-guide.md` and `migration-guide.md` as listed.
2. Edit `CLAUDE.md`, `README.md`, `packages/crypts-and-commits/README.md`, `docs/QUICKSTART.md` and `docs/CHANGELOG.md` as listed.
3. Update the world summary's Ruling bullet with `world_get` then `world_set_body`, and the c002 campaign body with `campaign_get` then `campaign_update`, changing only the named phrases.
4. Add the test assertions in `test_skills.py` and `test_docs.py`.
5. Re-run the narrowing search (`grep -rniE "lore/world|world's lore|become lore|name no lore|into lore|needs no lore|standing lore"` over `src/`, `CLAUDE.md`, `README.md`, `docs/` and the package README) and confirm that every remaining hit is intentional, such as a lore-specific example.
6. Run the full suite and ruff.

## Verification

- `pdm run pytest -q` passes, including the extended `test_skills.py` and new `test_docs.py` assertions and the existing workflow size-cap test. No skips or deletions.
- After `pdm run ruff format .`, `pdm run ruff check .` and `pdm run ruff format --check .` are clean.
- The step 5 search shows no remaining lore-only description of canonize; any leftovers are listed with a reason.
- `world_get` and `campaign_get` show only the named phrases changed. `boss_get b005` is unchanged.
- The deployed `.claude/skills/` and `.agents/skills/` copies are not edited; the developer is asked to redeploy at completion.

## Log

### Review - 2026-11-21T03:49:18Z - John Hoff

Independent lore review of c002/e007 (scripted, region crypts-and-commits): PASS-WITH-NOTES. clean-tests-and-lint is honored: Verification requires `pdm run pytest -q` with no skips or deletions, plus clean ruff check and format, and the plan adds tests without weakening any. skills-authored-only-in-templates is honored: only the packaged claude and codex world_planner templates are edited, the deployed .claude/skills and .agents/skills copies stay untouched, and the developer is asked to redeploy with `cac bootstrap init`. workflow-doc-source-of-truth is honored: workflow.md's one lore-only sentence about ruling links is updated, with headroom under the 45,000-character cap (about 44,057 bytes now), and the plan explains why tool-reference.md needs no change since behavior and contracts are unchanged. cli-mcp-parity and console-best-practices do not apply because no cli/ or mcp/ code changes. Sourcebook edits go through MCP only and b005 stays frozen. Notes: the new test_docs check for "rulings into lore" guards only against future regressions, because the phrase appears only in skill descriptions, which test_skills.py covers. Flagged but unverified: AGENTS.md, the Codex counterpart of CLAUDE.md, is not in the edit list or the step-5 search scope and may repeat the lore-only rulings and world-planner wording, so confirm it during execution.

### Opened - 2026-11-21T03:50:49Z - John Hoff

Opened with developer approval. The step 5 search will also cover AGENTS.md, per the reviewer's flag.

### Message - 2026-11-21T03:54:44Z - John Hoff

Implementation complete, pending developer confirmation.

- **Templates:**
  - Both world-planner descriptions now read "triage recorded rulings into lore, region or world updates", identical across flavors.
  - `workflow.md`: "Rulings name no lore, region or world records". The file is 43,253 bytes, under the 45,000 cap.
  - `branching-guide.md` step 7: "If the developer wants it to stand".
  - `migration-guide.md` row: "approved lore, region or world changes".
- **CLAUDE.md:** the rulings bullet ("name no lore, region or world records") and the world-planner bullet ("lore, region or world changes").
- **README.md:** the Rulings bullet ("into the world's lore, a region or the world summary") and step 7 ("lore, region or world context").
- **Package README:** "canonized into lore, region or world updates".
- **QUICKSTART.md:** "the reason no change is needed", plus a region-targeted canonize example (`c012-e005-ci-region`).
- **CHANGELOG.md:** the intro and Skills entry now include region.
- **Sourcebook:**
  - World summary Ruling bullet: "lore, region or world changes made". Nothing else changed.
  - c002 body: the intro reads "canonized into the world's lore, regions or world summary" and the Skills goal reads "creates or updates lore, regions or the world summary". Nothing else changed: membership and the Log are intact, and the out-of-scope bullet was left alone because it was not named.
  - b005 was not edited.
- **Tests:**
  - `test_skills.py` pins the new world-planner description in both flavors.
  - `test_docs.py` adds `test_guides_never_narrow_canonize_to_lore` across all four guides. It normalizes whitespace so phrases wrapped across lines are still caught.
- **Step 5 search** (now also covering `AGENTS.md`, per the reviewer): the only hits are the expanded phrases themselves. `AGENTS.md` has none.

**Verification:**
- pytest: 1702 passed.
- ruff format and check clean.
- The deployed skill copies were not edited.

### Message - 2026-11-21T03:56:25Z - John Hoff

Deviation at the developer's direction: after implementation, the developer asked for the whole c002 campaign body to be rewritten to reflect what was built, not only the two phrases named in the plan. The body (via `campaign_update`) now describes the delivered goals in detail:
- the full `ruling_*` tool set;
- prime and search details;
- the skills in both flavors;
- the docs, including `AGENTS.md` needing no change.

The rest of the rewrite:
- "Tentative encounter order" is replaced with the actual encounters e001–e007.
- A list of the four recorded rulings is added.
- The out-of-scope bullet is widened to "lore, a region, the world, a superseded ruling, or a boss".
- The intro notes that b005's frozen summary says "lore" and that ruling `c002-e007-canonize-targets-lore-region-world` widens canonizing to lore, region or world.

Membership (`b005-ruling-records`) and the empty Log are unchanged.

### Completed - 2026-11-21T03:57:20Z - John Hoff

Completed with developer confirmation. Verification passed:
- 1702 tests passed, ruff format and check clean.
- The narrowing search, also covering `AGENTS.md`, shows only the widened wording.
- `workflow.md` is under its cap at 43,253 bytes.
- The world summary changed only in its Ruling bullet; b005 is unedited.
- The deployed skill copies were not touched.

The c002 body was also rewritten at the developer's direction (logged above). The developer has been asked to redeploy the changed world-planner template with `cac bootstrap init`.
