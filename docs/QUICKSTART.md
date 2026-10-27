# Quickstart

Get Crypts and Commits (CAC) working in your own project in three steps.
This guide only covers getting an agent session up and running - once it is,
your coding assistant already knows the rest (its `world-manager` and
`campaign-manager` skills, and the `docs` MCP/CLI tool for deeper reference,
are all deployed for you by the last step below).

## 1. Install the package

```bash
pip install crypts-and-commits
```

This installs the `cac` CLI and the `cac-mcp` MCP server console script.

## 2. Bootstrap your project

From your project's root directory:

```bash
cac bootstrap init
```

This is a one-time, developer-run command (never run it from inside an agent
session) that sets up everything an agent needs:

- Creates `.sourcebook/` and seeds an empty `world.md`.
- Registers the `crypts-and-commits` MCP server for both Claude Code
  (`.mcp.json`) and Codex (`.codex/config.toml`), and deploys the Codex
  sourcebook-guard hook, which denies `apply_patch` edits targeting managed
  sourcebook files. It does not filter shell commands or ordinary-file patches
  whose content merely mentions sourcebook paths.
- Adds the `.sourcebook/` guardrail permissions to `.claude/settings.json`.
- Deploys the `world-manager` and `campaign-manager` agent skills into both
  `.claude/skills/` and `.agents/skills/`.

It's safe to run again later - re-running only fills in anything missing or
updates framework-owned files (like the skills) to a newer `cac` release;
your own edits to `.sourcebook/` content are never touched.

After upgrading CAC, run `cac bootstrap init` yourself to replace the packaged
hook script and upgrade its old Bash/apply_patch registration to apply_patch
only. Unrelated hooks and configuration are preserved. In Codex, review and
trust the updated project hook through `/hooks`, and re-enable it if it was
temporarily disabled. Agents must not run bootstrap or edit deployed hooks.
Managed sourcebook content must still be accessed through CAC's MCP/CLI
interfaces; narrower hook enforcement does not relax that workflow.

## 3. Hand off to your agent

Start a session with your coding assistant and ask it to flesh out the world
file - for example:

> Use the world-manager skill to help me write our world summary.

From here, your agent drives `.sourcebook/` for you: building out lore,
regions, and campaigns as work comes up. If you (or your agent) ever need the
full domain-model reference, it's one call away - `cac docs get workflow`, or
ask the agent to look it up.

### Optional branch settings

The world defaults to `main` for `merge_target_branch` and `planning` for
`planning_branch`. Inspect the effective values or store overrides through the
existing world commands:

```bash
cac world get
cac world set merge_target_branch trunk
cac world set planning_branch plans/team
cac prime get
```

MCP exposes the same values through `world_get`, `world_set`, and the world
portion of `prime_get`. Legacy worlds missing these attributes use the defaults
without being rewritten, so no migration or bootstrap rerun is needed. Existing
explicit values are preserved. New worlds record both defaults at initialization.
These settings configure intended branch names; setting them does not create or
switch branches or enforce a branching workflow.

### Capture future goals as bosses

Boss records capture goals before choosing a campaign:

```bash
cac boss create b001-improve-planning --body-file "notes/goal.md" --summary "Simplify planning."
cac boss get b001-improve-planning
cac boss update b001-improve-planning --body "Simplify planning." --summary "Simplify planning."
cac boss make-available b001-improve-planning
cac boss create b002-document-planning --body "Document the workflow." --summary "Document planning."
cac boss assign-dependency b002-document-planning b001-improve-planning
cac boss list
cac boss unassign-dependency b002-document-planning b001-improve-planning
cac boss withdraw b002-document-planning
cac boss reactivate b002-document-planning
cac boss withdraw b002-document-planning
cac boss archive b002-document-planning
cac boss list --include-archived
```

Create/update require a summary (at most 500 characters) and accept inline body,
`--body-file`, or an editor if neither body option is supplied. Use full names;
numbered names are optional and short refs are deferred. Make-available records
readiness even if prerequisites remain unsatisfied. Unassigned proposed/available
goals can be edited; available goals stay available. Linked, vanquished, withdrawn,
and archived goals cannot have their designs edited.

Archive accepts only unassigned withdrawn bosses. Archived names are retained;
get still reads them. There is no deletion/restoration operation. Missing storage
is empty; first create provisions it without migrating existing records.
All commands have matching `boss_*` MCP tools. See `cac docs get workflow` for
state guards, dependency validation, paging, and response contracts. Assignment,
campaign coupling, rumors operations, boss search/prime integration,
and automated numbering remain future work.

### Discover the next goal

Run `cac boss candidates` (MCP: `boss_candidates`) for a read-only JSON page of
summaries, eligibility, prerequisite states, and integrity diagnostics. Resume
with `cac boss candidates --cursor TOKEN` using the returned `next_cursor`.

Available, unassigned goals with vanquished direct prerequisites are eligible
when their reachable graph is sound. Proposed goals are `not_ready`; unsatisfied
available goals are `blocked`. Assigned/retired/archived goals are excluded roots,
but archived vanquished prerequisites still count. Numeric ordering is not priority.
Counts distinguish an empty collection from blocked or not-ready goals. Check
`healthy` and diagnostic/omission fields before treating the inventory as sound.
Hydrate named records with `cac boss get` or `cac campaign get`; discovery omits
bodies and bounds explanation lists. It neither selects work nor proves a goal's
implementation merged; confirm integration through your normal Git workflow.
