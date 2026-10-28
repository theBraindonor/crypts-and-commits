# Crypts and Commits Branching Guide

This guide explains how to use Git with Boss Edition. The [Workflow Reference
Guide](workflow.md) remains authoritative for domain rules, approval gates and
skill procedure. Read it through `docs_get("workflow")` / `cac docs get workflow`.
Exact tool and command contracts live in the [Tool Reference](tool-reference.md),
read through `docs_get("tool-reference")` / `cac docs get tool-reference`.
Read this guide through `docs_get("branching-guide")` / `cac docs get branching-guide`.
For an existing installation, start with the [Migration Guide](migration-guide.md).

## Branch roles and reasons

Inspect the current branch, worktree and effective world settings before acting.
`world_get` / `cac world get` exposes `merge_target_branch` (default `main`)
and `planning_branch` (default `planning`), including defaults absent from older
records. Store overrides through `world_set` / `cac world set`; this creates no
branches. Throughout this guide substitute the configured names for main/planning.
For example, `merge_target_branch=trunk` and `planning_branch=plans/team` means
registration and implementation integrate into trunk and goals evolve on plans/team.

| Branch | Work that belongs here | Campaign state |
| --- | --- | --- |
| main | Accepted integration history and shared registrations | No open campaign |
| planning | Goal capture/refinement, readiness, prerequisites, rumor distillation and planning-side archive | No open campaign |
| c012-search-tools-assignment | Register a draft campaign and reciprocal selected-boss links | Draft only |
| c012-search-tools | Campaign tactics, encounters, rumors and lifecycle outcomes | Its own campaign may be open; paused work stays here |

Create planning from synchronized main. Synchronize accepted merge-target history
before editing goals, selecting work or distilling rumors. Publish planning goals
through the project's normal integration policy before assignment registration.
The goal definitions must be visible in the history used to register their owner.
Assigned boss designs stay frozen; registration and campaign lifecycle update their
ownership/status metadata on campaign branches. Planning also owns the narrow
archive operation for integrated terminal campaigns and their current bosses.
It does not execute campaigns or revise their tactics.

world-manager supplies static context; world-planner owns goal planning and rumor
distillation; campaign-manager turns explicit selections into deliberate tactics.
Available means ready for consideration. Eligible also requires an intact graph,
no assignment and vanquished prerequisites. Neither state proves implementation
was integrated: inspect accepted history before relying on a prerequisite.

Endpoints are branch-agnostic. Core sees the checkout's single open campaign;
it neither inspects Git nor blocks an operation on the wrong branch. These branch
roles are skill guidance. Explain wrong-branch/detached-HEAD situations and reconcile
with the developer rather than silently switching, overwriting or adding new guards.
Existing authorization persists; reading this guide authorizes no Git publication,
merge, destructive cleanup or communication to others. Follow repository policy.

## Allocate numbers and check conflicts

Use canonical names such as `b007-search`, `c012-search-tools` and
`e001-index-search`. Boss and campaign numbers are independent project allocations;
encounter numbers start at e001 within each campaign. Existing targets accept
`b007`, `c012` and `c012/e001`; a bare e001 needs an explicit or active campaign.
Create names are literal. Legacy full names remain readable and need no bulk rename.

Skills choose numeric maximum plus one from complete inventories, including retained
archives. Use boss_list, campaign_list and encounter_list with include_archived=true
(CLI lists: `--include-archived`), follow every next_cursor, and use explicit campaign
context for encounter inventories. Also inspect known local/remote campaign branches
for reservations absent from records. Refresh remote refs when available and already
authorized; disclose offline or incomplete visibility. No central allocator exists.

Pad below 1000: after retained b999 comes b1000, even if b999 is archived. Never
reuse a retained allocation; timestamps, lexical ordering and search ranking do not
allocate numbers. A branch-only c020 reservation excludes c020 even without a record.
The matching c020-slug-assignment/c020-slug pair reserves one number, not two.
Reserve the -assignment suffix for registration branches. Numbers convey no priority.

Check at campaign creation, after branch integrations, and before completion; repeat
the last check after review fixes. Compare numeric IDs with different slugs, same-campaign
encounter numbers and reciprocal boss/campaign ownership. Two cleanly merged files can
still claim the same number or boss. Explain and reconcile such conflicts manually;
do not silently renumber history, rewrite managed files or treat a clean Git merge as
proof of logical consistency. MCP/CLI operations remain the managed-record interface.

## Worked path from goals to integrated work

The names below are illustrative allocations, not commands to reuse in another project.
Git creation/integration uses the repository's policy and existing authorization.
MCP names below have CLI fallbacks; body files are ordinary input notes, never direct
managed-file writes. Inspect exact command help where argument detail is needed.

1. On planning synchronized with main, use world-planner to capture b007-search and
   b008-search-docs with bodies, summaries and real prerequisites. Readiness is an
   explicit decision using boss_make_available / `cac boss make-available b007`.
   Use boss_candidates / `cac boss candidates` and hydrate goals with boss_get /
   `cac boss get b007`. Check accepted prerequisite implementation, not just local
   vanquished state. Publish the goals into main under normal integration policy.
2. Select both eligible goals explicitly. After inventory and collision checks,
   create c012-search-tools-assignment from updated main. Write tactics covering both
   goals, then campaign_create with name, body and bosses=[b007,b008]. CLI equivalent:
   `cac campaign create c012-search-tools --body-file notes/tactics.md --boss b007 --boss b008`.
   boss_assign_campaign / `cac boss assign-campaign` is the single-goal convenience.
   Registration creates a draft and reciprocal ownership, freezing the goal designs;
   it does not open a campaign or authorize encounters. Draft-only campaign_set_bosses
   replaces the entire group with a required reason; opening locks membership.
3. Integrate the small registration into main. Create c012-search-tools from updated
   main, or from the assignment branch and reconcile accepted registration before
   opening. The execution branch exactly matches the campaign's canonical name.
   After tactical decisions and authorization, campaign_open / `cac campaign open c012`
   opens it there. A bossless campaign can be created directly on its execution
   branch, skipping registration while retaining numbering/collision checks.
4. Draft e001-index-search and subsequent encounters. Each encounter retains explicit
   approval to launch a fresh independent review, separate approval to open, and
   developer confirmation to complete after verification. A passing plan review is
   not execution approval. Locked changes become recorded messages. Both scripted
   and unscripted kinds retain their canonical gates. See workflow for exact rules.
5. Capture discoveries on execution through rumors_create / `cac rumors create --campaign c012`
   with an explicit body or body file; replace an existing document through
   rumors_update / `cac rumors update --campaign c012`. Rumors are one freeform document per campaign,
   not automatic expansion of the chosen goals. Inspect through rumors_get /
   `cac rumors get --campaign c012`; preserve useful context.
6. Finish and verify encounters, run collision/ownership checks, and complete the
   campaign with its required postmortem through campaign_complete / `cac campaign complete`.
   Completion moves the selected group to vanquished. Integrate the completed branch
   into main using a PR or a local merge under the same policy. A PR host is optional.
   Completion alone does not establish integration. If pre-merge review requires
   changes, campaign_reactivate / `cac campaign reactivate c012 --message "Review fixes"`
   reopens the campaign on execution without unlocking membership/history. Use new
   follow-up encounters, verify, repeat collision checks, and complete again before merge.
7. Synchronize planning from accepted main. Distill integrated rumors with world-planner
   into developer-selected goals/refinements; do not automatically delete the rumors
   document, edit assigned goals or fabricate lineage. Archive only when the campaign
   is terminal, integrated and every encounter is terminal. campaign_archive /
   `cac campaign archive c012` archives its encounters and current bosses; released
   bosses owned by later attempts remain untouched. Rumors stay live. Standalone
   boss archive accepts unassigned withdrawn goals or valid externally completed
   roadmap goals. Archive restoration is deferred, not a deletion workaround.

## When the normal path changes

**Rejected registration, nothing merged.** Inspect whether registration actually
reached main and whether an execution branch exists. If it did not, synchronized
main/planning still contain unassigned goals. With the developer, revise the proposal
or retain an abandoned local attempt: abandon the draft through CAC on an appropriate
campaign branch, releasing local ownership with a reason. Preserve useful notes and
disclose surviving branch reservations. Do not publish rejection as accepted history
or automatically delete branches/records to reuse a number.

**Accepted registration, cancelled before execution.** Create the matching execution
branch from synchronized main, verify reciprocal ownership, and abandon the draft
with a reason through campaign_abandon / `cac campaign abandon`. No opening or
encounter is required merely to abandon a draft. Integrate that cleanup normally,
then synchronize planning before reselecting the released goals. Abandoned membership
lists remain historical; planning receives the outcome rather than abandoning campaigns.

**Legacy prototype open on main.** Read existing instructions, campaign and encounters,
including paused work. Agree how continued work moves to the matching execution branch
without losing history. An open encounter blocks campaign pause/closure: finish it or
abandon it with the developer before making the integration branch inactive. There is
no universal safe Git recipe for already-diverged histories. Reconcile deliberately,
preserve unnumbered names/references and do not invent bosses or retrofit open membership.
The library must not strand valid legacy records behind branch-dependent checks.

**Prerequisite completed only locally.** A vanquished goal on an unmerged execution
branch is insufficient. Inspect configured merge-target history and synchronize its
accepted implementation before selection on planning. If remote refresh is unavailable,
state the refs actually inspected and resolve uncertain integration with the developer.
Then recheck candidate health and ownership/numbers after integration.

## Independent clones, worktrees and indexes

Each checkout has its own records and active campaign. Separate execution worktrees
can each have one open campaign; this establishes no distributed claim, supervision
or globally consistent ownership across clones. Inspect known unpublished branches,
fetch only within authorization, and disclose what is invisible. Do not copy managed
records between worktrees by hand to resolve collisions. Use normal Git integration
and supported CAC operations, with deliberate developer repair for unsupported states.

After switching branches, index freshness is content-based. An inconsistent/stale
index is not proof the source records are missing or a reason to mutate them. Inspect
through ordinary APIs; route rebuilding to developer-run `cac index rebuild`, never an
agent rebuild or fabricated MCP tool. Goals and encounters remain readable through
their direct APIs without requiring search. Branch checks, local statuses and a clean
merge each provide limited evidence; report those limits when recommending next work.
