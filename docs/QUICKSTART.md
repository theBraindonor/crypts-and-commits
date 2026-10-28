# Quickstart

Get Crypts and Commits (CAC) working in your own project in three steps.
This guide only covers getting an agent session up and running - once it is,
your coding assistant already knows the rest (its `world-manager`, `world-planner`
and `campaign-manager` skills, and the `docs` MCP/CLI tool for deeper reference,
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

This is a developer-run setup command (never run it from inside an agent
session) that sets up everything an agent needs:

- Creates `.sourcebook/` and seeds an empty `world.md`.
- Registers the `crypts-and-commits` MCP server for both Claude Code
  (`.mcp.json`) and Codex (`.codex/config.toml`), and deploys the Codex
  sourcebook-guard hook, which denies `apply_patch` edits targeting managed
  sourcebook files. It does not filter shell commands or ordinary-file patches
  whose content merely mentions sourcebook paths.
- Adds the `.sourcebook/` guardrail permissions to `.claude/settings.json`.
- Deploys the `world-manager`, `world-planner` and `campaign-manager` skills into both
  `.claude/skills/` and `.agents/skills/`.

It's safe to run again later - re-running only fills in anything missing or
updates framework-owned files (like the skills) to a newer `cac` release;
your own edits to `.sourcebook/` content are never touched.

For an existing installation, first read the target release's
[Migration Guide](../packages/crypts-and-commits/src/cac/core/templates/docs/migration-guide.md).
An older installed guide may lack the new upgrade steps; obtain the target guide
from a verified source revision or distribution as it describes. Library upgrade,
developer-run redeployment, user-owned instruction edits and schema migration are
separate. Boss Edition keeps schema 1 and needs no bulk record conversion.

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
regions, future goals with world-planner, and chosen campaigns with campaign-manager.
If you (or your agent) ever need the
full domain-model reference, it's one call away - `cac docs get workflow`, or
ask the agent to look it up. Exact tool and command contracts are in
`cac docs get tool-reference`.

Read the [Branching Guide](../packages/crypts-and-commits/src/cac/core/templates/docs/branching-guide.md)
via `cac docs get branching-guide` / `docs_get("branching-guide")` before choosing
campaign work. It shows goal publication, assignment registration and execution,
with configured names and collision checks. These conventions are skill guidance;
endpoints neither switch branches nor grant Git integration authorization.

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
`--body-file`, or an editor if neither body option is supplied. Create with literal
full names; existing targets accept short refs. Recommended skill workflows allocate
numbered names, while endpoints also accept legacy names. Make-available records
readiness even if prerequisites remain unsatisfied. Unassigned proposed/available
goals can be edited; available goals stay available. Linked, vanquished, withdrawn,
and archived goals cannot have their designs edited.

Archive accepts unassigned withdrawn bosses or valid externally completed roadmap
goals. Archived names are retained;
get still reads them. There is no deletion/restoration operation. Missing storage
is empty; first create provisions it without migrating existing records.
All commands have matching `boss_*` MCP tools. See `cac docs get workflow` for
state guards and dependency validation, and `cac docs get tool-reference` for
paging and response contracts.
Rumors operations and boss search/plural active-boss prime integration are available.
Skills allocate numbers from complete retained inventories and known branch
reservations; endpoints never allocate them. world-planner also supports incremental
roadmap capture; see the migration guide for evidence/provenance and legacy limits.

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

### Use short references

Existing targets accept `b001`, `c001`, and `c001/e001`; bare `e001` uses an
explicit or active campaign. For example:

```bash
cac boss get b001
cac campaign get c001
cac encounter get c001/e001
cac encounter list --campaign c001
cac boss assign-dependency b002 b001
```

Qualified encounter refs supply their own campaign, even when another campaign
is active. A conflicting explicit campaign is an error. Live and archived
records participate; duplicate numeric IDs are ambiguous. Use full canonical
names to inspect colliding records. Returned identity metadata shows canonical
names and usable refs, or null with a reason. Lists retain canonical items with
parallel identities; candidates include identity in their existing bounded JSON.

Create names remain literal: `cac boss create b001-new-goal ...` creates that
name; it never expands into an existing record. Newly written dependencies use
canonical names. Reference resolution does not allocate, rename, discover Git
branches, migrate, or assign campaigns. See `cac docs get tool-reference` for exact grammar,
legacy-name precedence, context rules, operation coverage, and response budgets.

### Pursue a boss with a campaign

Publish goal planning into the configured merge target, confirm eligibility and
integrated prerequisites, and allocate an unused campaign number. On its assignment
branch, prepare tactical notes and promote the selected boss:

```bash
cac boss assign-campaign b001 c001-planning --body-file "notes/campaign.md"
cac campaign get c001
```

Promotion creates a draft with reciprocal links; it does not open it or create
encounters. For several bosses, campaign create accepts repeated --boss options.
Integrate accepted registration, then open the campaign on its exact-name execution
branch after authorization. Bossless campaigns may skip registration. Follow each
encounter's separate review/open/completion approvals and verify work before its
outcome. Completion vanquishes the selected group; abandonment releases it for a
new campaign while retaining the old campaign's history. See the Branching Guide
for local-merge and hosted-PR paths, both subject to repository policy.

For feedback on a completed, unarchived campaign, use
`cac campaign reactivate c001 --message "Address PR feedback"`. Earlier closing
entries and completed encounters remain intact; create new follow-up encounters,
then verify and complete again before integration. On synchronized planning,
archive integrated terminal campaigns to archive their current bosses
and terminal encounters together. Archiving an abandoned old attempt never
changes a reassigned boss. Origin/reverse links prevent campaign deletion.

Capture execution discoveries using `cac rumors create --campaign c001 --body-file notes/rumors.md`
(or update for an existing document). world-planner distills integrated rumors
on planning without automatically deleting them or expanding campaign scope.

`boss_assign_campaign` and `campaign_reactivate` provide MCP parity. Same current
assignment retries are read-only and never replace campaign content. Inconsistent
ownership fails with diagnostics; recovery failures identify residual records
for explicit repair. These operations use local records, with no automatic Git,
merge verification, allocation, or record migration.
