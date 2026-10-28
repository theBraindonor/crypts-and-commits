# Crypts and Commits Sourcebook Migration Guide

**Current sourcebook schema version: 1**

## Purpose

The `.sourcebook` domain model is versioned. `world.md` carries a
`schema_version` frontmatter attribute, stamped onto every sourcebook
`cac bootstrap init` creates from scratch. A sourcebook created before this
attribute existed has no such value; treat a missing attribute as version 1 -
the format that existed before versioning was introduced.

`cac bootstrap init` checks an *existing* `world.md`'s `schema_version`
against the version the installed `cac` package expects, and reports if the
sourcebook is behind (needs migration) or ahead (the installed `cac` is
older than the sourcebook and should be upgraded). Bootstrap only reports -
it never edits `world.md` itself. Migrating the content is the coding
assistant's job, guided by this document, via the `world-manager` skill.

There is deliberately no separate migration *tool*: a hand-maintained
migration engine would be complex, rarely exercised, and far less adaptable
than having the agent read this guide and make the changes itself. This
document is the source of truth an agent consults to do that.

## Maintaining this guide

Whenever `SOURCEBOOK_SCHEMA_VERSION` (`core/config.py`) is bumped, add a new
`## Migrating from version N to N+1` section below, in the same change, and
update the "Current sourcebook schema version" line above to match. Each
section should give the agent every concrete change needed to bring a
sourcebook fully onto the new version - what changed structurally, and
exactly how to apply it.

## Boss Edition upgrade and workflow adoption

Boss Edition is the feature target for these instructions. The development
package currently declares 0.2.0, but the Boss Edition release number and tag
have not been selected. Do not assume that an installed or published 0.2.0
contains this guide. Record the actual source version and the target release
or verified commit before upgrading; substitute the selected release when it
exists. This guide makes no claim that a new release is already published.
Python >=3.11, Git, the project's package manager and access to the selected
distribution/source are prerequisites. Respect its dependency and Git policy.

### Obtain the target instructions before trusting old skills

An old `cac docs get migration-guide` returns the old package's guide, which
may know nothing about Boss Edition. Use the target artifact instead:

1. Locate the intended release tag or full commit in the project's trusted
   repository, https://github.com/theBraindonor/crypts-and-commits. In a separate
   source checkout at that verified revision, read
   `packages/crypts-and-commits/src/cac/core/templates/docs/migration-guide.md`
   and its siblings branching-guide.md, workflow.md and tool-reference.md. A tag alone is insufficient
   if it lacks those files or predates the required feature contracts.
2. Alternatively obtain the selected wheel through the project's approved
   package source, verify its identity under local policy and inspect
   `cac/core/templates/docs/migration-guide.md` inside it. Reading an extracted
   artifact does not modify the live sourcebook or require bootstrap.
3. Preserve the target version/commit and source of these instructions in the
   adoption plan. Do not feed new records to the old library while comparing
   versions. If the target guide cannot be obtained or verified, resolve that
   missing input before dependent upgrade work.

The [Branching Guide](branching-guide.md) provides worked Git examples and edge
cases; [workflow.md](workflow.md) is the canonical lifecycle/procedure authority,
and [tool-reference.md](tool-reference.md) holds exact tool and command contracts.
After installation the equivalent routes are `docs_get("branching-guide")` /
`cac docs get branching-guide`, `docs_get("workflow")` / `cac docs get workflow`,
and `docs_get("tool-reference")` / `cac docs get tool-reference`.
Ordinary workflow adoption does not require changing the schema version.

### Upgrade in distinct stages

1. **Inventory and plan.** Read existing CLAUDE.md/AGENTS.md files and imports,
   world settings, installed package identity, deployed skills/hooks, open and
   paused campaigns and their encounters through supported APIs. Record current
   Git branch/worktree state and known local/remote reservations. Preserve user
   changes. Agree how in-flight work continues and what upgrade/adoption is
   authorized before performing dependent changes. Use the normal encounter
   approval gates when the project requires them; existing authorization persists.
2. **Upgrade the library.** Install the selected artifact using the project's
   package manager/lockfile policy. Restart/reconnect persistent MCP consumers
   and agent sessions as needed so they load that package, rather than continuing
   to execute old code. Verify installed distribution metadata and `cac --help`,
   `cac docs list`, and `cac docs get migration-guide` against the target guide.
   This stage does not update local instructions or deploy skills/hooks.
3. **Redeploy framework assets.** The developer runs `cac bootstrap init` from
   the project root after upgrading. This refreshes framework-owned skill/hook
   files, preserving unrelated configuration under bootstrap's merge rules.
   It does not migrate records or rewrite user-owned CLAUDE.md/AGENTS.md.
   The developer reviews/trusts the updated Codex hook through `/hooks` and
   re-enables it if needed. Custom unrecognized hook registrations need separate
   inspection; do not assume deployment rewrites them. Agents neither run
   bootstrap nor edit deployed copies/trust settings. Reopen sessions as needed
   to discover world-manager, world-planner and campaign-manager.
4. **Update local instructions deliberately.** Apply the mapping below to the
   files actually present and their established import structure. Preserve
   unrelated policy, tool preferences and local exceptions. Explain targeted
   changes rather than replacing files with a framework template. Reconcile
   conflicts with the developer; upgrading does not authorize new publication,
   branch cleanup or messages to others.
5. **Adopt branches and goals as needed.** Follow the Branching Guide with the
   world's effective merge-target/planning names. Inventory legacy work first;
   do not blindly rename history or attach bosses to already-open campaigns.
   Incremental roadmap recording below is optional. Configuring names does not
   create/switch branches, prove integration or require wholesale adoption.
6. **Check schema separately.** Boss Edition's additive contracts retain schema
   1. Missing schema_version means 1, and missing boss storage is empty/lazy.
   Do not suspend a guardrail, rewrite records, run bootstrap as migration or
   stamp a new schema just for this upgrade. If an actual version-specific
   structural migration is required by a later target guide, follow its exact
   steps and the generic approval/capture/restoration procedure below instead.

### Targeted instruction mapping

Read first; the examples describe replacements for obsolete CAC clauses, not
complete instruction-file templates. Link deep details rather than duplicating
the full workflow into every project.

| Older CAC guidance | Targeted replacement or clarification |
| --- | --- |
| Plan every future idea as a campaign; only two skills exist | Route static context to world-manager, goal/roadmap/readiness and rumor triage to world-planner, and explicit tactical selection/execution to campaign-manager. |
| An available boss is immediately executable, or one campaign always has one boss | Availability records readiness; selection checks prerequisites/graph/integration and exclusive ownership. A draft can choose zero/one/many bosses; tactics address the whole group. Assignment freezes designs; opening locks draft membership. |
| Open campaigns directly on main | Main/planning/assignment have no open campaign under the recommended workflow. Register selected bosses on the campaign's -assignment branch, then open on the exact campaign-name execution branch. Bossless campaigns may skip registration. |
| Pick the next number from the visible list or reuse an old number | Skills use complete retained/archive-inclusive inventories plus known campaign branch reservations, numeric max plus one and per-campaign encounters. Check collisions at creation, after integration and before completion/recompletion; resolve manually. Rumor numbers may collide across branches and are renumbered on planning. |
| Edit assigned goal notes when discoveries appear | Capture discoveries from anywhere as standalone rumors (`rumor_create`); triage integrated rumors on planning with world-planner into selected goals or dismissals, without deletion or scope expansion. |
| Completion proves merged work, or review fixes overwrite completed history | Verify integration separately. Complete before implementation integration; reactivate completed campaigns for pre-merge fixes, add follow-up encounters, verify and complete again. Retain history and group membership. |
| Codex hook blocks shell access to managed paths | The packaged hook now denies apply_patch file-operation targets inside managed sourcebook paths. Shell calls are not filtered. MCP/CLI-only access remains binding; narrower enforcement grants no bypass. Developer redeployment and hook review/trust are separate. |

A shared guidance replacement might read:

> Before nontrivial CAC work, orient with world-manager. Use world-planner for
> goal planning, roadmap capture and integrated rumor triage; use
> campaign-manager for explicit tactical selection and encounter execution.
> Follow the installed Branching Guide via docs_get("branching-guide") or
> cac docs get branching-guide, with workflow as the procedural authority.
> Access managed records through the crypts-and-commits MCP tools first and
> equivalent cac CLI only as fallback. Bootstrap and index rebuild remain
> developer-only; existing encounter review/open/completion approvals persist.

Keep this in the established shared instruction source. For a CLAUDE-only
project, update just its obsolete clauses; do not create AGENTS.md merely to
match a sample. For AGENTS-only, make the equivalent targeted edits there.
If AGENTS.md imports CLAUDE.md (as this development repo does), update shared
CAC guidance in CLAUDE.md and retain AGENTS.md's import and genuine provider
overrides. If the import direction is reversed, keep that source instead.
For independent files, inspect each and avoid erasing intentional differences.
Link world-planner through the project's deployed skill location and link the
guide through docs retrieval (or a verified target-source link during upgrade).
These examples grant no permission to edit deployed framework skills.

### Preserve in-flight work and verify adoption

Inspect open/paused campaigns and encounters before branch changes. An open
unnumbered prototype on main needs an agreed transition to continued execution
on its matching branch and an inactive merge target; an open encounter prevents
pausing/closing the campaign. Finish or abandon that encounter only within its
ordinary approvals. Preserve history and references; do not invent a boss,
retrofit ownership onto an open campaign, bulk rename records or require a
universal Git repair recipe. See the Branching Guide's rejected registration,
registered cancellation and legacy-work examples. Core remains branch-agnostic.

Before declaring adoption done, verify the installed package and connected MCP
consumer use the chosen target, all three registered guides are readable without
normal-budget truncation, and deployed skill owners match local instructions.
Inspect the effective hook registration/script and developer trust state without
triggering a destructive managed-file test. Confirm unrelated hooks/settings
remain, the apply_patch-only boundary is accurately described, and any actually
disabled migration guardrails were restored. Inspect effective world settings,
campaign/encounter state and reciprocal boss links via supported MCP/CLI reads;
disclose incomplete remote/integration knowledge. Verify legacy work still has
a valid continuation path. A guide walkthrough does not prove live repairs.

Actual adoption in this development repository is a subsequent encounter. This
guide does not choose a release number, deploy assets, rewrite local instructions
or mutate managed records just by being retrieved.

## Hook redeployment is separate from record migration

The current packaged Codex guard denies only `apply_patch` file targets inside
the managed sourcebook. It does not filter shell calls or ordinary-file patch
content mentioning managed paths. The MCP/CLI-only instruction still applies;
this change narrows automated enforcement, not the workflow.

After a library upgrade, the developer runs `cac bootstrap init` to replace
the framework-owned script and upgrade recognized legacy Bash/apply_patch hook
registrations to apply_patch only, preserving unrelated hooks/settings. The
developer then reviews/trusts the changed hook through `/hooks` and re-enables
it if necessary. The agent must not run bootstrap or edit deployed copies.
This deployment change requires no sourcebook schema migration and does not
authorize suspending any guardrail or directly editing managed records. Record
migrations still follow the explicit approval and restoration procedure below.

## Generic migration procedure

This procedure applies to every migration, regardless of which
version-to-version section(s) below it in this document. Follow it in
addition to, not instead of, the specific steps in each applicable section.

A real migration is very likely to need direct edits to `.sourcebook/`
files. The generic per-object setters the MCP/CLI surface exposes
(`world_set`, `lore_set_summary`, and similar) cannot perform arbitrary
structural changes a schema change may require - renaming a frontmatter key
across every file of a type, restructuring body sections, and the like. This
means a migration is the one sanctioned exception to the project's normal
`.sourcebook`-is-MCP/CLI-only guardrail, and that exception must be entered
and exited deliberately:

1. **Get explicit, informed approval before disabling any guardrail
   mechanism.** This is a bigger ask than a normal encounter approval - it
   is turning off a project safety mechanism, not just approving a plan.
   Explain to the developer which mechanism(s) will be disabled and why,
   and wait for an explicit yes.
2. **Record the current state of every guardrail mechanism in force for
   this session before touching anything**, so it can be restored exactly:
   - Claude Code: the `Edit(.sourcebook/**)` deny rule in
     `.claude/settings.json`.
   - Codex: the `PreToolUse` sourcebook-guard hook registration in
     `.codex/config.toml` (and the hook script it points to).
3. **Temporarily remove or disable the applicable guardrail mechanism(s).**
4. **Perform the migration's direct file edits**, following the
   version-specific section(s) below that apply.
5. **Restore every guardrail mechanism touched in step 3 to its exact prior
   state immediately afterward - unconditionally**, even if the migration
   is aborted or fails partway through. Do not leave the project
   unguarded because a migration didn't finish cleanly.
6. **Only after the guardrail is restored**, verify the migrated content
   through normal MCP/CLI calls (`world_get`, `lore_list`/`lore_get`,
   `region_list`/`region_get`, `campaign_list`/`campaign_get`,
   `encounter_list`/`encounter_get`, as applicable to what changed), and set
   the new version with `world_set("schema_version", "<new version>")`
   (MCP) or `cac world set schema_version <new version>` (CLI).
7. **Confirm with the developer** that the guardrail was restored and the
   migration verified, before considering the migration done.

## Version-specific migrations

Boss planning storage is additive within schema version 1. Upgrading the library
provides boss create/read/update, planning transitions, withdrawn-boss archive,
and dependency operations. Missing boss storage is empty and directories are
created lazily. Existing worlds, campaigns, and encounters are not rewritten;
no record migration, guardrail suspension, or bootstrap rerun is needed for
these operations. Optional campaign origin boss links and lifecycle coupling are
also additive within schema 1: legacy campaigns remain bossless, with no inferred
goals, rewritten history, guardrail suspension, or bootstrap migration. Upgrade the
library for promotion and completed-campaign reactivation; workflow/skill adoption
follows the separate stages above. Older libraries do not manage these new contracts.

Within prerelease Boss Edition, campaigns now use canonical `bosses` lists while
each boss keeps one current scalar `campaign`. This reader accepts legacy `boss`
scalars and absent membership without writes; ordinary campaign mutations normalize
to `bosses`, but no-op membership requests preserve bytes. Both fields together
are an error, requiring deliberate reconciliation. No bulk conversion, schema bump,
guardrail suspension, or bootstrap is needed. Do not use older one-boss libraries
on plural records or downgrade without a developer-planned conversion. Campaign
API results expose bosses; prime replaces active_boss/active_boss_diagnostic with
active_boss_names/active_bosses/active_boss_diagnostics. Update consumers with the
library. Preserve abandoned campaign lists as history; they are not current claims.

### Adopt an existing roadmap

The e014 recording contract retains schema 1. No bulk conversion, guardrail
suspension, or bootstrap migration is required. Existing records without
provenance remain readable and are not rewritten. Pre-e014 libraries must not
mutate roadmap-recorded bosses: they cannot validate the provenance or enforce
its historical-completion/archive rules. Downgrade requires deliberate developer
conversion; optional fields alone do not establish backward compatibility.

Record only the relevant goals, incrementally, through boss_record / cac boss
record. Supply the body, summary, explicit progress (planned/in_progress/completed),
source description/reference, and message explaining capture and outcome evidence.
Planned/in_progress goals start proposed and require the normal readiness decision.
Completed goals start unassigned vanquished without synthetic campaigns/encounters;
they satisfy prerequisites, including after supported standalone archival.
CAC records supplied evidence, not independent proof of external work or a Git merge.

For example, record delivered b001-storage from roadmap.md#storage with release
evidence and a known completed_on date; next record planned b002-search with
depends_on=[b001]; finally record in_progress b003-ui with its outside-work reference.
Each new name is literal and create-only; duplicate live/archived names fail.
Enter prerequisite records first; unknown relationships stay in prose. Inspect the
result with boss_get before proceeding. No roadmap fetch, extraction, or full import
is implied. Provenance progress remains the original snapshot, not live status.

created_on/updated_on reflect CAC recording now. Optional completed_on is a known
YYYY-MM-DD date for completed progress only, never future (UTC); unknown is null.
Never invent/backdate audit fields. Historical completions are frozen like ordinary
completed bosses; no undo/edit/restore API is added. Mistakes require deliberate
developer repair, preserving graph/index consistency; this grants agents no direct
managed-file access. Use normal supported operations for incomplete goals.

Capture references to existing campaigns as context. Adopting already-open legacy
campaign ownership is deferred; recording never changes campaign membership or
status. Existing draft-only membership, single ownership, and lifecycle guards
remain. Planning/branch guidance, skills deployment, and local-instruction adoption
follow the separate stages above; agents must not run bootstrap.

No mandatory record migrations are documented yet; sourcebook schema remains 1.
The compatible optional-field changes above do not require a bulk rewrite.
When `SOURCEBOOK_SCHEMA_VERSION` is next bumped,
its section goes here, in this form:

```
## Migrating from version 1 to 2

<What changed structurally, and exactly how to apply it - which files,
which attributes or body sections, in what order.>
```
