---
archived: false
campaign: c001-boss-edition
created_by: John Hoff
created_on: '2026-10-28T04:11:56Z'
depends_on:
- e020-adopt-boss-edition-workflow-in-this-repo
kind: scripted
name: e022-correct-campaign-deletion-guard-wording
regions:
- crypts-and-commits
status: open
updated_by: John Hoff
updated_on: '2026-10-28T13:00:59Z'
---

## Requirements

Correct the campaign-deletion sentence in both packaged `campaign-manager` skill templates so it matches the code and the Workflow Reference Guide. This resolves the e019 finding carried forward in e020's log.

- Files: `packages/crypts-and-commits/src/cac/core/templates/skills/claude/campaign_manager/SKILL.md` (lines 114-115) and `packages/crypts-and-commits/src/cac/core/templates/skills/codex/campaign_manager/SKILL.md` (lines 112-113). Both currently say: "Deletion is not unconditional: linked/historical memberships, reverse boss claims and archived state are protected."
- Actual behavior (`core/coupling.py`, `campaign_operation`, around lines 404-410): deletion is refused only when the campaign's `bosses` list (current or historical membership) is non-empty or a boss claims the campaign. The archived-state guard explicitly exempts `delete`, so an archived bossless campaign can be deleted. `workflow.md` line 177 already states the code behavior: "A campaign can be deleted only when its `bosses` list (current or historical membership) is empty and no boss claims it."
- Change only that clause in both templates, identically. Replace it with wording to this effect: deletion is refused while the campaign has a non-empty `bosses` list (current or historical) or a reverse boss claim; archiving does not protect a bossless campaign from deletion. Keep the rest of the paragraph unchanged: MCP has no prompt, CLI `--yes`, no core-guard bypass, and "Do not use deletion as a rollback/renumber shortcut".
- Keep both templates' lines within their existing wrap width, and keep the two provider variants' wording identical apart from tool-name prefixes.

Out of scope: any `core` behavior change (archived campaigns stay deletable when bossless); `workflow.md`/`tool-reference.md` (already accurate); deployed `.claude/skills/` / `.agents/skills/` copies; running bootstrap; other skill wording.

## Rationale

The skills currently tell agents that archived campaigns are protected from deletion. They are not, so an agent could rely on a guard that doesn't exist, or wrongly refuse a deletion the developer asked for, based on a false premise. The code and the owning doc (`workflow.md`) already agree. Correcting the skill wording, rather than adding a core guard, is the smallest change that makes skills, docs and code consistent, and that consistency is required by c001's completion criterion. A core change would need its own design discussion and is not proposed here.

## Plan

1. Confirm the branch is `c001-boss-edition` and the working tree is clean.
2. Edit the sentence in the two template files named above (template paths only, never deployed copies).
3. Diff the two templates' edited paragraph to confirm they match each other apart from tool prefixes. Grep both templates to confirm "archived state are protected" is gone.
4. Run the existing skill/docs tests first (`pdm run pytest packages/crypts-and-commits/tests/core/test_skills.py -q`), then the full gate: `pdm run pytest -q`, `pdm run ruff check .`, `pdm run ruff format .`.
5. Commit the template change and the e022 sourcebook record as "Correct campaign deletion guard wording in skills (e022)". Ask the developer to run `cac bootstrap init` to redeploy; the assistant does not run it.

## Verification

- Both template files state that deletion is blocked by a non-empty `bosses` list or a reverse boss claim, and that archiving does not protect a bossless campaign. Neither still claims "archived state" is protected.
- The edited paragraph matches `workflow.md` line 177 and the code in `core/coupling.py`.
- Only the two template files and the sourcebook record changed (`git diff --stat`).
- `pdm run pytest -q` passes; `ruff check .` reports zero errors; `ruff format .` changes nothing.
- The developer redeploys with `cac bootstrap init`, and the deployed copies then match the templates (normalized blob comparison).
- The developer confirms completion.

## Log

### Review - 2026-10-28T12:57:27Z - John Hoff

Reviewed against clean-tests-and-lint, skills-authored-only-in-templates, workflow-doc-source-of-truth, cli-mcp-parity and console-best-practices. The defect is real: both campaign_manager templates (claude lines 114-115, codex lines 112-113) say archived state protects a campaign from deletion. In fact core/coupling.py campaign_operation exempts delete from the archived guard and refuses deletion only for a non-empty bosses list or a reverse boss claim, which matches workflow.md lines 176-178. The Plan edits only the two template paths, keeps the provider variants identical, and leaves the deployed copies and the bootstrap redeploy to the developer, which satisfies skills-authored-only-in-templates. It explicitly justifies not changing workflow.md and tool-reference.md: this is a wording correction that aligns the skills with the owning doc and makes no doc statement inaccurate, which satisfies workflow-doc-source-of-truth. Plan and Verification include the full pytest and ruff check/format gate. cli-mcp-parity and console-best-practices are not triggered. Notes: tool-reference.md being accurate was only partly checked (campaign-delete rows); the committed e022 sourcebook record should contain only changes made through MCP.

### Opened - 2026-10-28T12:58:21Z - John Hoff

Opened with developer approval. Working tree clean apart from this encounter's own review record.

### Message - 2026-10-28T13:00:59Z - John Hoff

Executed Plan steps 1-4. Both campaign_manager templates now read: "Deletion is not unconditional: a non-empty bosses list (current or historical membership) or a reverse boss claim blocks it; archiving does not protect a bossless campaign. MCP has no interactive deletion prompt; CLI ..." (rest of paragraph unchanged). The two paragraphs diff identical; "archived state are protected" no longer appears under templates/skills. Reviewer note resolved: a full grep of tool-reference.md for "delet" finds no archived-protection claim (only the confirmation section and the delete rows), so it stays accurate. test_skills.py 10 passed; full suite 1564 passed; ruff check clean; ruff format left 286 files unchanged. Changed files: the two templates plus this sourcebook record.
