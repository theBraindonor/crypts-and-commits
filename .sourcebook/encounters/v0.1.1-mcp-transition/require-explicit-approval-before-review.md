---
campaign: v0.1.1-mcp-transition
created_by: John Hoff
created_on: '2026-07-25T19:54:06Z'
depends_on: []
name: require-explicit-approval-before-review
regions: []
status: completed
updated_by: John Hoff
updated_on: '2026-07-25T20:00:10Z'
---

## Requirements

- The campaign-manager skill must never spawn the independent reviewer subagent (the
  `draft` -> `reviewed` lore-review gate) automatically right after an encounter is
  drafted. It must stop and get the user's **explicit** go-ahead first, every time it is
  about to spawn that subagent - including the first review of a fresh draft and any
  re-review after a `REJECT`/`NOT-REVIEWABLE` verdict and subsequent `cac encounter
  update`.
- This gate is specifically about *launching* the reviewer subagent. It does not change
  what happens once the reviewer has already returned: a `PASS-WITH-NOTES` verdict still
  auto-transitions via `cac encounter review <name> --message "..."` without a separate
  approval pause, per the existing documented behavior.
- Both flavors of the skill document need the fix, since both currently instruct
  immediate auto-spawn: `.claude/skills/campaign-manager/SKILL.md` (step 1 of the
  numbered `draft` -> `reviewed` procedure) and `.agents/skills/campaign-manager/SKILL.md`
  (its Codex-flavored equivalent, same step numbering, different subagent-launch wording).
- `CLAUDE.md`'s `campaign-manager` skill description (under "Agent skills") should be
  checked and, if it undersells or omits this gate, updated so the project-level summary
  doesn't imply automatic review.
- No functional/CLI code changes are needed - the `cac` CLI has no concept of "spawn a
  subagent," so this is purely a documentation/process fix in the skill instructions (and
  possibly CLAUDE.md).

## Rationale

The reviewer subagent has been launched several times without the user's explicit
approval, even though a prior session already logged this exact correction as
assistant-side memory ("don't spawn the reviewer without asking first"). That memory is
scoped to one assistant's own persistence and isn't visible to a fresh session, a
different assistant, or the Codex-flavored skill copy under `.agents/` - so the
correction kept needing to be re-learned. The actual fix has to live in the instructions
every agent reads before acting (the SKILL.md files themselves, and CLAUDE.md if it also
describes the flow), not in one assistant's private memory, so the gate is enforced
regardless of which agent or session is driving the work.

## Plan

1. In `.claude/skills/campaign-manager/SKILL.md`, under `## Encounter Lifecycle` /
   `**\`draft\` -> \`reviewed\`**`: insert a new first step, before the existing "Spawn a
   fresh reviewer" step, requiring the agent to stop and get the user's explicit
   confirmation before launching the reviewer subagent. Renumber the remaining steps
   (current 1-4 become 2-5). Apply the same explicit-confirmation requirement to the
   REJECT/NOT-REVIEWABLE re-review path described immediately after the numbered list
   ("revise the draft ... and spawn a fresh reviewer again") so a second pass through the
   gate isn't exempt.
2. Apply the equivalent edit to `.agents/skills/campaign-manager/SKILL.md`, keeping its
   existing Codex-flavored phrasing (no `Task` tool references) and matching step
   numbering/renumbering.
3. Read `CLAUDE.md`'s "Agent skills" section (the `campaign-manager` bullet). If its
   one-line description of the draft -> reviewed gate reads as fully automatic, add a
   short clause noting the reviewer subagent requires explicit user approval before it is
   spawned. If the existing wording is already gate-agnostic enough not to contradict
   this, leave it unchanged and note that in the Verification step rather than editing
   for its own sake.
4. Re-read both edited SKILL.md files in full to confirm consistent step numbering, no
   leftover references to the old step order, and that the `PASS-WITH-NOTES`
   auto-transition wording (which must NOT change) still reads correctly after the
   renumbering.

## Verification

- Manual read-through of both `SKILL.md` files confirms: a new, unambiguous "stop and get
  explicit user approval before spawning the reviewer subagent" instruction exists ahead
  of every subagent-launch point (initial draft and REJECT/NOT-REVIEWABLE re-review), step
  numbering is consistent, and the post-verdict auto-transition behavior on
  `PASS-WITH-NOTES` is unchanged.
- Confirm `CLAUDE.md` either already reads consistently with the new gate or has been
  updated to reflect it.
- `pdm run ruff check .` and `pdm run ruff format .` stay clean, and `pdm run pytest -q`
  still passes, per the world's `clean-tests-and-lint` lore gate (no source/test files are
  expected to change, so this should be a no-op check).

## Log

### Review - 2026-07-25T19:56:19Z - John Hoff

Reviewed against the sole applicable lore item, clean-tests-and-lint (world-assigned; no regions are assigned to this encounter, so no region lore applies). The Plan is doc-only (two SKILL.md files plus a conditional CLAUDE.md check) and its Verification section correctly commits to pdm run pytest -q, pdm run ruff check ., and pdm run ruff format . as a completion gate, consistent with the lore's requirement - no conflicts found. Verified against the current committed content of both SKILL.md files that the Plan's described insertion point (before the existing 'Spawn a fresh reviewer' step) and renumbering (1-4 -> 2-5) match reality. One item is flagged but unverified rather than checked: whether an unassigned region (e.g. covering .claude/skills/ or .agents/skills/) exists that should have been assigned to this encounter and might carry additional lore - this was out of the bounded reading surface since the encounter itself cites no regions.

### Completed - 2026-07-25T20:00:10Z - John Hoff

Added an explicit step 1 to the draft -> reviewed procedure in both .claude/skills/campaign-manager/SKILL.md and .agents/skills/campaign-manager/SKILL.md: stop and get the user's explicit go-ahead before spawning the reviewer subagent, applying to both the first review pass and any re-review after REJECT/NOT-REVIEWABLE. Renumbered subsequent steps (2-5) and left the PASS-WITH-NOTES auto-transition behavior unchanged, since that gate is about launching the reviewer, not what happens after it returns. CLAUDE.md's campaign-manager description was checked and left unchanged - it doesn't claim automatic review. Verified: pdm run ruff format . / ruff check . clean, pdm run pytest -q passed 504/504.
