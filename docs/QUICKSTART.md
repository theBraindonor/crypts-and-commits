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

After upgrading the library, restart or reconnect any long-running MCP servers
and agent sessions so they load the new package. A server started on the old
version keeps serving the old tools and docs list.

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

These settings only name the branches the recommended workflow uses. CAC never
creates or switches branches and does not enforce a branching workflow. Before
you use the recommended planning workflow, create the configured planning branch
yourself under your own Git policy, and do the same for the merge target if it
isn't your existing default branch.

### Capture future goals as bosses

A boss is a goal you capture and refine before any campaign commits to it. A
typical lifecycle:

1. **Create** it as `proposed`. A routing summary (at most 500 characters) is
   required; the body comes from `--body`, `--body-file`, or your editor if
   neither is given.

   ```bash
   cac boss create b001-improve-planning --body-file "notes/goal.md" --summary "Simplify planning."
   cac boss get b001-improve-planning
   ```

2. **Refine** it. Update replaces the body and summary together:

   ```bash
   cac boss update b001-improve-planning --body "Simplify planning." --summary "Simplify planning."
   ```

3. **Mark it ready.** `make-available` records readiness even if prerequisites
   are not yet satisfied:

   ```bash
   cac boss make-available b001-improve-planning
   ```

4. **Link prerequisites.** Dependencies are validated as a graph:

   ```bash
   cac boss create b002-document-planning --body "Document the workflow." --summary "Document planning."
   cac boss assign-dependency b002-document-planning b001-improve-planning
   cac boss list
   cac boss unassign-dependency b002-document-planning b001-improve-planning
   ```

5. **Retire it** if plans change. Withdraw an unassigned goal, reactivate it
   back to `proposed`, or withdraw and archive it for good:

   ```bash
   cac boss withdraw b002-document-planning
   cac boss reactivate b002-document-planning
   cac boss withdraw b002-document-planning
   cac boss archive b002-document-planning
   cac boss list --include-archived
   ```

Good to know:

- Unassigned `proposed` and `available` goals can be edited, and an available
  goal stays available. A goal's design freezes once it is linked to a campaign,
  vanquished, withdrawn or archived.
- Archive accepts unassigned withdrawn bosses and valid externally completed
  roadmap goals. Archived names stay reserved and `get` still reads them. There
  is no delete or restore operation.
- Create with literal full names; existing targets also accept short refs (see
  below). The recommended skill workflows allocate numbered names from complete
  retained inventories and known branch reservations. Endpoints never allocate
  numbers, and legacy unnumbered names stay valid.
- A project with no bosses has empty storage; the first create provisions it
  without migrating existing records.
- To adopt an existing roadmap, use world-planner's incremental roadmap capture.
  The migration guide covers evidence, provenance and legacy limits.
- Every command has a matching `boss_*` MCP tool. Bosses are searchable, and
  `prime get` includes every boss selected by the active campaign. Rumors are
  covered in the next section.

State guards and dependency validation are in `cac docs get workflow`; paging
and response contracts are in `cac docs get tool-reference`.

### Capture ideas as rumors

A rumor is a backlog note, "we think X should be done", that isn't a goal yet.
Capture one whenever an idea comes up: during an encounter, in a review, from a
customer, or from the running project. You can capture on any branch.

1. **Capture** it with a numbered name, a summary (at most 500 characters) and
   a free-text origin naming who or what raised it. The body is optional.
   Allocate the number as the numeric maximum plus one over
   `cac rumor list --include-archived`.

   ```bash
   cac rumor create r001-cache-wheels --summary "Cache wheel builds in CI" --origin "Retro, sprint 12" --body-file "notes/rumor.md"
   cac rumor list --status open
   cac rumor get r001
   ```

2. **Refine** an open rumor. Update replaces the body, summary and origin
   together:

   ```bash
   cac rumor update r001 --summary "Cache wheel builds in CI" --origin "Retro, sprint 12" --body-file "notes/rumor.md"
   ```

3. **Triage on planning.** Rumors captured on different branches can arrive
   with the same number. Renumber collisions first; this works only for open or
   dismissed rumors, because a promoted rumor's number is already settled. Then
   either promote each rumor to a boss, or dismiss it with a reason.
   Promotion takes two steps: create or refine the boss, then link the rumor to
   it. The boss must be unassigned and `proposed` or `available`, and many
   rumors may share one boss. The link is stored only on the rumor; the boss
   record isn't changed.

   ```bash
   cac rumor renumber r001-cache-wheels r004-cache-wheels
   cac boss create b007-faster-ci --summary "Faster CI." --body-file "notes/goal.md"
   cac rumor promote r004 b007 --message "Part of the CI goal"
   cac rumor dismiss r002 --message "Superseded by the new build system"
   ```

4. **Undo or retire.** `cac rumor reopen r004 --message "..."` returns a
   promoted or dismissed rumor to open and clears its boss link.
   `cac rumor archive r002` retires a promoted or dismissed rumor read-only.
   There is no delete.

Similar rumors are never merged automatically, because repetition is a signal.
Every transition message is kept in the rumor's `history`. Rumors are
searchable with `cac index search PHRASE --type rumor`, and every command has a
matching `rumor_*` MCP tool. world-planner does the planning-side triage, and
any skill can capture.

### Discover the next goal

`cac boss candidates` (MCP: `boss_candidates`) answers "what could we work on
next?" It returns a read-only JSON page of summaries, eligibility, prerequisite
states and integrity diagnostics. When the result has a `next_cursor`, continue
with `cac boss candidates --cursor TOKEN`.

How to read it:

- **Eligible**: available, unassigned, every direct prerequisite vanquished, and
  a sound reachable graph.
- **`not_ready`**: still proposed.
- **`blocked`**: available, but prerequisites are not yet satisfied.
- Assigned, retired and archived goals are excluded as roots, but an archived
  vanquished prerequisite still counts as satisfied.
- Counts distinguish an empty collection from one where every goal is blocked
  or not ready. Check `healthy` and the diagnostic/omission fields before
  treating the inventory as sound.
- Numeric order is not priority.

Discovery omits bodies and bounds its explanation lists, so hydrate anything you
want to read with `cac boss get` or `cac campaign get`. It doesn't select work,
and it can't prove a goal's implementation merged; confirm integration through
your normal Git workflow.

### Use short references

Wherever an existing record is expected, numbered records accept short refs:
`b001`, `c001` and `c001/e001`. A bare `e001` uses the explicit or active
campaign. For example:

```bash
cac boss get b001
cac campaign get c001
cac encounter get c001/e001
cac encounter list --campaign c001
cac boss assign-dependency b002 b001
```

- A qualified encounter ref carries its own campaign, even when another campaign
  is active. A conflicting explicit campaign is an error.
- Live and archived records both resolve. Duplicate numeric IDs are ambiguous;
  use full canonical names to inspect colliding records.
- Results include identity metadata: canonical names and usable refs, or null
  with a reason. Lists keep canonical items with parallel identities, and
  candidates include identity in their bounded JSON.
- Create names stay literal: `cac boss create b001-new-goal ...` creates exactly
  that name and never expands into an existing record. Newly written
  dependencies use canonical names.
- Resolution never allocates, renames, discovers Git branches, migrates, or
  assigns campaigns.

Exact grammar, legacy-name precedence, context rules, operation coverage and
response budgets are in `cac docs get tool-reference`.

### Pursue a boss with a campaign

The recommended flow, which the skills walk through with you:

1. **Plan.** Publish goal planning into the configured merge target. Confirm the
   goal is eligible and its prerequisites are integrated, and allocate an unused
   campaign number.
2. **Select.** On the campaign's assignment branch, write tactical notes and
   promote the boss into a draft campaign:

   ```bash
   cac boss assign-campaign b001 c001-planning --body-file "notes/campaign.md"
   cac campaign get c001
   ```

   Promotion creates a draft with reciprocal links; it doesn't open the campaign
   or create encounters. Select every boss you want before opening the campaign:
   membership locks when the campaign opens. To pursue several bosses together, create the campaign
   with a repeated `--boss` option:

   ```bash
   cac campaign create c002-planning-docs --boss b003 --boss b004 --body-file "notes/campaign.md"
   ```

3. **Execute.** Integrate the accepted registration, then open the campaign on
   its exact-name execution branch once you have authorized it. A bossless
   campaign may skip registration. Each encounter still gets its own review,
   open and completion approvals, and work is verified before its outcome is
   recorded.
4. **Finish.** Completion vanquishes every selected boss. Abandonment releases
   them for a new campaign while keeping the old campaign's history.

The [Branching Guide](../packages/crypts-and-commits/src/cac/core/templates/docs/branching-guide.md)
covers the local-merge and hosted-PR paths, both subject to repository policy.

**Review feedback.** To address feedback on a completed, unarchived campaign,
reopen it:

```bash
cac campaign reactivate c001 --message "Address PR feedback"
```

Earlier closing entries and completed encounters remain intact. Create new
follow-up encounters, then verify and complete again before integration.

**Archiving.** On synchronized planning, archive integrated terminal campaigns;
this archives their current bosses and terminal encounters together. Archiving
an abandoned old attempt never changes a boss that was reassigned.

**Deletion.** A campaign can be deleted only when its `bosses` list (current or
historical membership) is empty and no boss claims it. Archiving does not
protect a bossless campaign. Deletion is never a rollback or renumbering
shortcut.

**Discoveries.** Capture ideas that come up during execution as rumors (see
"Capture ideas as rumors" above). Capturing a rumor never expands the
campaign's scope.

**MCP and recovery.** `boss_assign_campaign` and `campaign_reactivate` provide
MCP parity. Retrying the same current assignment is read-only and never replaces
campaign content. Inconsistent ownership fails with diagnostics, and recovery
failures identify residual records for explicit repair. These operations use
local records only, with no automatic Git, merge verification, allocation, or
record migration.
