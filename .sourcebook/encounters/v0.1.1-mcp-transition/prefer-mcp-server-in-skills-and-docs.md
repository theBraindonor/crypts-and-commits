---
campaign: v0.1.1-mcp-transition
created_by: John Hoff
created_on: '2026-07-25T21:36:24Z'
depends_on: []
name: prefer-mcp-server-in-skills-and-docs
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-07-25T21:49:08Z'
---

# Encounter

## Requirements

- Update both Claude Code skills under `.claude/skills/` (`world-manager`,
  `campaign-manager`) and their Codex-native mirrors under `.agents/skills/`
  so that the `cac` MCP server (already covering every command family except
  `bootstrap`, per the `cli-mcp-parity` region lore) is documented as the
  primary way an agent interacts with `.sourcebook`, with the `cac` CLI kept
  only as an explicit fallback for when the MCP server is not
  available/connected for a session.
- Do not duplicate the CLI's own `--help` documentation (flag names, syntax,
  etc.) inside skill prose. Each command entry should name the MCP tool and
  its parameters (matching the underlying Python function signature, e.g.
  `lore_create(name, body, summary)`) plus whatever *workflow* semantics
  aren't obvious from the tool alone (e.g. the "draft the summary and get
  developer approval before calling" rule, paging/cursor behavior,
  campaign-defaulting, mutating-vs-read command restrictions,
  status-lifecycle gating) - the same semantics apply whether invoked via MCP
  or CLI. Reserve literal CLI flag syntax for a one-line fallback note only
  (e.g. "CLI fallback: `cac lore create --help`").
- Preserve every existing workflow rule verbatim in substance: the
  disclosure ladder, the lore-review reviewer-subagent gate (including its
  approval choreography), the campaign/encounter status lifecycles, the
  encounter list/no-search caveat, and the bootstrap-is-developer-only rule.
  This is a documentation/interface change, not a process change.
- Update the reviewer subagent prompt template (embedded in both
  `campaign-manager` variants) so the reviewer also primes itself via the
  MCP tools first (`world_get`, `encounter_get`, `prime_applicable_lore`,
  `lore_get`, `region_get`), falling back to the CLI equivalents only if MCP
  is unavailable in the reviewer's own session.
- For the Claude-specific (`.claude/skills/`) variants: reference the MCP
  tools using Claude Code's actual invocable names (`mcp__cac__<tool>`, e.g.
  `mcp__cac__world_get`) and extend each `allowed-tools` frontmatter line to
  permit them (matching the `mcp__cac` entry already allowed project-wide in
  `.claude/settings.json`), keeping the existing `Bash(cac *)` (and, for
  `campaign-manager`, `Task`) entries for the CLI-fallback and
  reviewer-subagent paths.
- For the Codex-native (`.agents/skills/`) variants: reference the MCP tools
  by their bare registered names (e.g. `world_get`) since Codex's MCP
  invocation surface doesn't share Claude Code's `mcp__<server>__` naming;
  keep the existing "Command execution" section but reframe it to state the
  MCP-first/CLI-fallback precedence explicitly, still noting the `pdm run
  cac ...` invocation detail for this dev repo's CLI fallback.
- Update `CLAUDE.md`'s "Guardrail: `.sourcebook/` is CLI-only" and
  "Architecture: the `cac` package" sections: the MCP server (`mcp/`) is no
  longer a placeholder - it now covers every domain except `bootstrap` - so
  replace forward-looking "eventually"/"future" language describing it with
  present-tense language describing it as the primary interaction layer, CLI
  retained as fallback. Do not change the technical-enforcement caveat about
  `Edit`/`Write` denial in `.claude/settings.json` - that is a separate,
  not-yet-done follow-up and stays out of scope here.
- Update `CLAUDE.md`'s "## Agent skills" section to note the parallel
  Codex-native copies under `.agents/skills/` (currently undocumented there)
  alongside the Claude Code originals under `.claude/skills/`, and describe
  both as MCP-first/CLI-fallback.
- Update `AGENTS.md` to state Codex should call the `cac` MCP server's tools
  (per `.mcp.json`) as the primary interface for `.sourcebook` work, shelling
  out to the `cac` CLI only when the MCP server isn't connected for the
  session - consistent with the skill-level change.
- Out of scope: any change to `.claude/settings.json` / permission
  enforcement, any change to `core/`/`cli/`/`mcp/` source code (all commands
  already exist on both sides per `cli-mcp-parity`), and the still-pending
  "move skills into `templates/skills/`" migration noted in `CLAUDE.md`
  (unrelated, separately gated).

## Rationale

The active campaign (`v0.1.1-mcp-transition`) exists to move `.sourcebook`
interaction from CLI shell-outs to an MCP server, working toward "the coding
assistant should have no awareness of the `.sourcebook` directory's existence
at all." The prior encounter
(`expand-mcp-server-to-lore-region-campaign-encounter`) finished the
server-side half of that: every CLI command except `bootstrap` now has a
matching MCP tool, and the new `cli-mcp-parity` region lore keeps that
property enforced going forward. That encounter's own Rationale explicitly
deferred this exact step: "It sets up a later encounter (not this one) to
migrate the `world-manager`/`campaign-manager` skills themselves to call the
MCP tools instead of shelling out to `cac`." This encounter is that
migration - the client-side half, plus the two top-level docs (`CLAUDE.md`,
`AGENTS.md`) that describe the guardrail and point agents at the skills.
Keeping the CLI as an explicit, still-documented fallback (rather than
deleting the CLI instructions outright) matches the project's own stated
interim state: the MCP server should be preferred, but an agent must still
be able to fall back to the CLI if the server isn't available for a given
session. Avoiding duplicated `--help`-level detail keeps the skill files
from drifting out of sync with the CLI's own docstrings - the CLI remains
the single source of truth for its own exact usage.

## Plan

1. Rewrite `.claude/skills/world-manager/SKILL.md`:
   - Frontmatter `allowed-tools`: `Bash(cac *)` -> `Bash(cac *), mcp__cac`.
   - Replace the "Work exclusively through the `cac` CLI" intro line with
     MCP-first/CLI-fallback wording.
   - Rewrite the World/Lore/Regions/Prime bullet lists: each entry names the
     `mcp__cac__<tool>` tool and its parameters, keeps the workflow-semantic
     sentences (summary-approval rule, paging/cursor contract,
     "assign-world means global", etc.), and appends a one-line CLI fallback
     pointer (e.g. "CLI fallback: `cac lore create --help`") instead of the
     current full flag syntax.
   - Leave the "bootstrap is developer-only" and "disclosure ladder"
     sections' substance unchanged, only touching tool-name references
     inside them.
2. Mirror the same structural rewrite in `.agents/skills/world-manager/SKILL.md`,
   but: no `allowed-tools` frontmatter (matches current absence), tool names
   bare (`world_get`, not `mcp__cac__world_get`), and keep/reframe the
   existing "## Command execution" section to state the MCP-first/CLI-fallback
   precedence (MCP tools are the primary interface; `cac ...`/`pdm run cac
   ...` is the fallback).
3. Rewrite `.claude/skills/campaign-manager/SKILL.md`:
   - Frontmatter `allowed-tools`: `Bash(cac *), Task` -> `Bash(cac *), Task,
     mcp__cac`.
   - Same MCP-first/CLI-fallback intro change.
   - Rewrite Campaigns/Encounters bullet lists the same way (tool name +
     params + workflow semantics + one-line CLI fallback), preserving the
     campaign-defaulting, mutating/read command distinctions, and full
     status-lifecycle sections verbatim in substance.
   - Update the reviewer subagent prompt template's priming bullet list to
     call `world_get`/`encounter_get`/`prime_applicable_lore`/`lore_get`/
     `region_get` MCP tools first (as `mcp__cac__<tool>` in this variant),
     falling back to the CLI forms only if MCP is unavailable to the
     reviewer.
4. Mirror the same rewrite in `.agents/skills/campaign-manager/SKILL.md`
   (bare tool names, existing "Command execution" section reframed,
   reviewer template updated to Codex's own subagent-spawn wording, which is
   already distinct from the Claude variant - keep that difference, only
   change the tool-priming bullets).
5. Update `CLAUDE.md`:
   - "Guardrail" section: replace the "an MCP server ... is meant to
     eventually replace" sentence with present-tense wording (the MCP server
     now exists and covers every command except `bootstrap`; it is the
     primary interaction layer, CLI is the fallback), leaving the
     `Edit`/`Write`-enforcement caveat paragraph's substance about deferred
     technical enforcement untouched (still true, separate scope).
   - "Architecture" section: change the `mcp/` bullet from "placeholder for
     a future MCP server" to a description matching its actual structure
     (`server.py`'s `_TOOL_MODULES`, one module per domain, thin-wrapper
     pattern) and its now-primary role.
   - "Agent skills" section: mention the parallel `.agents/skills/`
     Codex-native copies alongside `.claude/skills/`, and restate both as
     MCP-first/CLI-fallback.
6. Update `AGENTS.md`'s "Codex-specific overrides" bullet list to add an
   explicit MCP-first/CLI-fallback statement for `.sourcebook` interaction
   (call the `cac` MCP server's tools per `.mcp.json` as primary;
   `cac`/`pdm run cac` CLI only when MCP isn't connected), consistent with
   the skill-level change.
7. Re-read all six changed files end-to-end for internal consistency (no
   stale "CLI-only" phrasing left unaddressed, no broken cross-references)
   before verification.

## Verification

- `pdm run pytest -q` passes and `pdm run ruff check .` / `pdm run ruff
  format .` are clean, per the `clean-tests-and-lint` world lore (this
  encounter touches no Python source, so this simply confirms no
  regression).
- Manually diff each of the six changed files against its prior version and
  confirm: (a) no literal CLI flag-syntax documentation was newly introduced
  beyond a one-line fallback pointer per command, (b) every command family
  from the CLI's `--help` surface still has a corresponding documented MCP
  tool entry, (c) all workflow rules (disclosure ladder, reviewer-subagent
  gate and its approval steps, campaign/encounter lifecycles,
  bootstrap-is-developer-only) remain intact in substance.
- Confirm `.claude/skills/*/SKILL.md` and `.agents/skills/*/SKILL.md` stay
  behaviorally aligned (same tool coverage and workflow rules), differing
  only in tool-name prefix convention and the Codex-specific subagent-spawn
  wording already present before this change.

## Log

### Review - 2026-07-25T21:39:36Z - John Hoff

Reviewed against all three applicable lore items resolved via cac prime applicable-lore (clean-tests-and-lint, cli-mcp-parity, console-best-practices). The Plan is a documentation-only change (six named files: both .claude/.agents skill pairs, CLAUDE.md, AGENTS.md) with no core/cli/mcp source edits, so cli-mcp-parity's CLI-change trigger and console-best-practices (scoped to cac/cli/* Console usage) are not implicated - verified independently that CLI and MCP domain modules already mirror each other 1:1 except the permanently CLI-only bootstrap, matching the Plan's stated premise. clean-tests-and-lint is directly honored via the Verification section's pytest/ruff regression check. Cross-checked all six target files plus .claude/settings.json and .mcp.json against the Plan's factual claims about current state (frontmatter, existing sections, MCP server registration) and found no discrepancies. No lore conflicts identified; PASS-WITH-NOTES.

### Message - 2026-07-25T21:41:17Z - John Hoff

Clarification from developer on the reviewer's flagged note: CLAUDE.md's guardrail section currently claims both Edit and Write are denied for .sourcebook/** in .claude/settings.json, but only Edit actually is - there is no Write deny in reality (Claude Code's permission system has no separate Write-deny mechanism to configure here). When touching the Guardrail section's wording in this encounter's Plan step 5, correct that claim to state only Edit is denied, rather than leaving or perpetuating the inaccurate Edit/Write phrasing.

### Message - 2026-07-25T21:48:11Z - John Hoff

Verification complete: pdm run pytest -q (563 passed), ruff check . and ruff format . --diff both clean. Cross-checked every mcp__cac__<tool> reference in the two .claude SKILL.md files against the actual registered tool names in packages/crypts-and-commits/src/cac/mcp/*.py - exact match, no gaps, no stale names. Manually diffed .claude vs .agents SKILL.md pairs for both skills - the only deltas are the intended ones (tool-name prefix convention, the .agents-only Command execution section, and the pre-existing Codex-specific reviewer-subagent wording). Six files touched: .claude/skills/{world-manager,campaign-manager}/SKILL.md, .agents/skills/{world-manager,campaign-manager}/SKILL.md, CLAUDE.md, AGENTS.md. Also incorporated the developer's guardrail correction: CLAUDE.md now states only Edit (not Edit/Write) is denied on .sourcebook/** in .claude/settings.json.

### Completed - 2026-07-25T21:49:08Z - John Hoff

Completed: rewrote all four SKILL.md files (.claude and .agents variants for world-manager and campaign-manager) to document the cac MCP server's tools as primary, with a one-line CLI --help fallback pointer per command instead of duplicated flag syntax; all workflow rules preserved verbatim. Updated CLAUDE.md's Guardrail, Architecture, and Agent skills sections to present-tense MCP-primary/CLI-fallback language, correcting the guardrail's Edit/Write claim to Edit-only per developer note. Updated AGENTS.md's Codex overrides to state the same MCP-first/CLI-fallback precedence. Verification passed: pytest -q (563 passed), ruff check/format clean, and every mcp__cac__<tool> reference in the skill docs cross-checked 1:1 against the actual registered MCP tool names with no gaps.
