---
campaign: v0.1.4-formal-workflow-pipeline
created_by: John Hoff
created_on: '2026-07-28T05:09:09Z'
depends_on: []
name: require-gates-documented-in-skills
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-07-28T05:18:04Z'
---

## Requirements

- The "Explicit user gates" section of the Workflow Reference Guide
  (`packages/crypts-and-commits/src/cac/core/templates/docs/workflow.md`)
  must state, as a standing requirement, that each of the three gates it
  describes (before spawning the independent reviewer, before opening the
  encounter, before marking the encounter complete) must be explicitly and
  literally present in the wording of every implementation-specific skill
  template that carries the encounter lifecycle (`campaign_manager/SKILL.md`
  under both `templates/skills/claude/` and `templates/skills/codex/`) — not
  merely implied by, or left to inference from, this document.
- The addition must make clear that a skill template edit which touches the
  encounter lifecycle is expected to preserve all three gates' stop-and-ask
  wording, and that dropping or softening one silently is a defect, not a
  simplification.
- No change to CLI/MCP behavior, status lifecycles, or skill *procedure*
  itself is in scope — the three gates already exist, in both the doc and
  both skill templates (confirmed by inspection before drafting this
  encounter). This is a documentation-only reinforcement, not a behavior
  change.

## Rationale

The active campaign's motivation already names a recurring failure mode: the
gate-1 approval (before spawning the reviewer subagent) has occasionally been
bypassed in practice. The Workflow Reference Guide exists so implementation
skills are authored *against* a shared spec rather than drifting independently
(see `workflow-doc-source-of-truth` lore) — but the current "Explicit user
gates" section only describes the gates themselves; it doesn't say anything
about *how* that spec is supposed to reach the skills that enforce it. Making
explicit that each gate's stop-and-ask instruction must appear verbatim-in-
spirit in the relevant skill template closes that gap: it turns "the skill
should probably mention this" into a checkable requirement any future skill
edit (or review of one) can be held to, reinforcing the gates for the
assistant rather than leaving them as something it might infer.

## Plan

1. Edit `packages/crypts-and-commits/src/cac/core/templates/docs/workflow.md`,
   in the "Explicit user gates" section (after the numbered list of three
   gates, before the "What is *not* separately gated" paragraph): add a new
   paragraph stating that each of the three gates must be explicitly written
   into the relevant skill template's procedure text (`campaign_manager` for
   all three, since all three fall within the encounter lifecycle it owns),
   under both `templates/skills/claude/` and `templates/skills/codex/`; that
   this is what "explicit" means in practice — present in the skill's own
   wording, not left implicit or inferred from this document; and that a
   skill-template edit touching the encounter lifecycle must preserve all
   three gates' stop-and-ask instructions.
2. Cross-check the current `campaign_manager` skill templates (both flavors)
   against the three gates as documented, to confirm no drift exists today
   between this document and the skills it's supposed to be authored against.
   No skill edit is expected as a result — this step is verification, not
   remediation — but if a genuine gap is found, note it in the Verification
   section results and flag it to the user rather than silently patching
   skill content beyond what this encounter's Requirements describe.
3. No other files should need to change: this is a doc-only addition, so no
   `mcp/`, `cli/`, or `core/` behavior is touched, and `skills-authored-only-
   in-templates` and `cli-mcp-parity` don't apply.

## Verification

- Read back the edited "Explicit user gates" section and confirm the new
  paragraph is present, accurately reflects the three existing gates by name,
  and names both `templates/skills/claude/campaign_manager/SKILL.md` and
  `templates/skills/codex/campaign_manager/SKILL.md` as the enforcement
  target.
- Re-read both current `campaign_manager` SKILL.md templates and confirm each
  of the three gates' stop-and-ask wording is still genuinely present (the
  cross-check from Plan step 2) — report the result even though no skill edit
  is anticipated.
- `pdm run pytest -q` and `ruff check .` / `ruff format .` clean, per
  `clean-tests-and-lint` (a markdown-only change is expected to leave both
  untouched, but the gate still runs).

## Log

### Review - 2026-07-28T05:11:42Z - John Hoff

Reviewed against all five applicable lore items (clean-tests-and-lint, workflow-doc-source-of-truth, skills-authored-only-in-templates, cli-mcp-parity, console-best-practices); no conflicts found. cli-mcp-parity and console-best-practices are correctly out of scope since no cli/mcp or console code is touched. The Plan's edit targets workflow.md's "Explicit user gates" section directly (self-consistent with workflow-doc-source-of-truth, since it doesn't itself change skill procedure or other code), and its cross-check step correctly treats the skill templates as read-only verification rather than an edit, per skills-authored-only-in-templates. Verification correctly runs the clean-tests-and-lint gate despite being a doc-only change. Independently confirmed by reading the two named skill templates and the named doc section that the encounter's core factual premise holds today: all three gates' stop-and-ask wording is genuinely present, verbatim-in-spirit, in both templates/skills/claude/campaign_manager/SKILL.md and templates/skills/codex/campaign_manager/SKILL.md, and the doc's insertion point (after the three-gate list, before "What is not separately gated") matches the Plan's description exactly.

### Opened - 2026-07-28T05:15:41Z - John Hoff

User approved opening, with a request to strengthen the added workflow.md paragraph beyond the drafted Plan's wording: the emphasis should explicitly address durability across future skill modification and regeneration (i.e. the requirement must survive a skill template being rewritten or reworked, not just be checked once at authoring time), not merely state that the gates must appear in the skill text.

### Completed - 2026-07-28T05:18:04Z - John Hoff

Added a paragraph to the "Explicit user gates" section requiring all three gates be written explicitly into both campaign_manager skill templates (claude and codex), framed to survive future modification or regeneration of those templates, not just checked once at authoring time. Cross-checked both current templates and confirmed all three gates already present verbatim-in-spirit, so no skill edit was needed. pdm run pytest -q (693 passed) and ruff check/format clean.
