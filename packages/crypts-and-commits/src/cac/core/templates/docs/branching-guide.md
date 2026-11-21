# Crypts and Commits Branching Guide

This guide explains how to use Git with Boss Edition. The [Planning Workflow](planning-workflow.md)
and [Development Workflow](development-workflow.md) own domain rules and procedure.
Read them on demand through `docs_get("planning-workflow")` /
`cac docs get planning-workflow` or `docs_get("development-workflow")` /
`cac docs get development-workflow`. [workflow](workflow.md) is a short router.
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
| planning | Goal capture/refinement, readiness, prerequisites, rumor and ruling triage and planning-side archive | No open campaign |
| c012-search-tools-assignment | Register a draft campaign and reciprocal selected-boss links | Draft only |
| c012-search-tools | Campaign tactics, encounters, captured rumors and rulings, and lifecycle outcomes | Its own campaign may be open; paused work stays here |

Create planning from synchronized main. Synchronize accepted merge-target history
before editing goals, selecting work or triaging rumors and rulings. Publish planning goals
through the project's normal integration policy before assignment registration.
The goal definitions must be visible in the history used to register their owner.
Assigned boss designs stay frozen; registration and campaign lifecycle update their
ownership/status metadata on campaign branches. Planning also owns the narrow
archive operation for integrated terminal campaigns and their current bosses.
It does not execute campaigns or revise their tactics.

world-manager supplies static context; world-planner owns goal planning and rumor
and ruling triage; campaign-manager turns explicit selections into deliberate tactics. Any
branch may capture rumors; only planning renumbers, promotes, dismisses or archives them.
Rulings are captured only on an execution branch whose campaign is open, when the
developer confirms a decision; only planning canonizes, notes or archives them.
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

Use canonical names such as `b007-search`, `c012-search-tools`,
`e001-index-search` and `r031-cache-wheels`. Boss, campaign and rumor numbers are
independent project allocations; encounter numbers start at e001 within each
campaign. Existing targets accept `b007`, `c012`, `r031` and `c012/e001`; a bare
e001 needs an explicit or active campaign.
Create names are literal. Legacy full names remain readable and need no bulk rename.

Skills choose numeric maximum plus one from complete inventories, including retained
archives. Use boss_list, campaign_list, encounter_list and rumor_list with
include_archived=true (CLI lists: `--include-archived`), follow every next_cursor, and
use explicit campaign context for encounter inventories. Also inspect known local/remote campaign branches
for reservations absent from records. Refresh remote refs when available and already
authorized; disclose offline or incomplete visibility. No central allocator exists.

Pad below 1000: after retained b999 comes b1000, even if b999 is archived. Never
reuse a retained allocation; timestamps, lexical ordering and search ranking do not
allocate numbers. A branch-only c020 reservation excludes c020 even without a record.
The matching c020-slug-assignment/c020-slug pair reserves one number, not two.
Reserve the -assignment suffix for registration branches. Numbers convey no priority.

Rumors are the exception to branch reservations: any branch may capture them, so
two branches can allocate the same rumor number. That collision is expected. After
integration, fix it on planning with rumor_renumber / `cac rumor renumber r031
r032-cache-wheels`, which accepts open or dismissed rumors only. Promotion happens on
planning, so a promoted rumor's number is already settled and is never renumbered.

Rulings take no number of their own. A ruling is named `cNNN-eNNN-slug` from the
open campaign and the encounter where the decision was made (`e000` for a
campaign-level decision), and those numbers are already settled on the execution
branch, so cross-branch collisions are not expected and there is no ruling
renumber. Create refuses a name already used by a live or archived ruling. Rulings
take full names only; `c012` or `c012/e003` never resolves to a ruling.

Check at campaign creation, after branch integrations, and before completion; repeat
the last check after review fixes. Compare numeric IDs with different slugs, same-campaign
encounter numbers and reciprocal boss/campaign ownership. Two cleanly merged files can
still claim the same number or boss. Explain and reconcile such conflicts manually;
do not silently renumber history (explicit rumor renumbering on planning is the only
renumbering operation), rewrite managed files or treat a clean Git merge as proof of
logical consistency. MCP/CLI operations remain the managed-record interface.

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
   and unscripted kinds retain their canonical gates. See development-workflow for exact rules.
5. Capture discoveries on execution as standalone rumors. Allocate the next number
   from every rumor_list(include_archived=true) page, then use rumor_create /
   `cac rumor create r031-cache-wheels --summary "Cache wheel builds" --origin "c012
   execution" --body-file notes/rumor.md`. A rumor records an idea for later; it is
   not automatic expansion of the chosen goals. Edit an open rumor with rumor_update
   and inspect it with rumor_get / `cac rumor get r031`.
   When the developer confirms an answer to an open question or choice during
   execution (a plan choice, an encounter or boss open question, or the reason for
   overriding a reviewer REJECT), record it in the same exchange with ruling_create /
   `cac ruling create c012-e003-cache-key-format --summary "Key caches by lockfile
   hash" --origin "Developer, c012 execution" --body-file notes/ruling.md`. The
   campaign must be open, and a nonzero encounter number must name an existing
   encounter in that campaign; use `e000` when no encounter applies. Edit a
   recorded ruling with ruling_update. A ruling never replaces the encounter log
   or a rumor, and with no open campaign the right capture is a rumor.
6. Finish and verify encounters, run collision/ownership checks, and complete the
   campaign with its required postmortem through campaign_complete / `cac campaign complete`.
   Completion moves the selected group to vanquished. Integrate the completed branch
   into main using a PR or a local merge under the same policy. A PR host is optional.
   Completion alone does not establish integration. If pre-merge review requires
   changes, campaign_reactivate / `cac campaign reactivate c012 --message "Review fixes"`
   reopens the campaign on execution without unlocking membership/history. Use new
   follow-up encounters, verify, repeat collision checks, and complete again before merge.
7. Synchronize planning from accepted main. Triage integrated open rumors with
   world-planner: list them with rumor_list / `cac rumor list --status open`, and
   renumber collisions first. To act on one, create or refine a developer-selected
   unassigned boss, then rumor_promote / `cac rumor promote r031 b009`; many rumors
   may share a boss, and the boss record is not written. Otherwise rumor_dismiss /
   `cac rumor dismiss r031 --message "Out of scope"`. Archive resolved rumors with
   rumor_archive. Never delete rumors, edit assigned goals or fabricate lineage.
   Triage integrated recorded rulings the same way: list them with
   ruling_list(status="recorded") / `cac ruling list --status recorded` (prime also
   shows them until triaged) and read each with ruling_get. If the developer wants
   it to stand, make the approved lore, region or world changes through
   world-manager, then ruling_canonize / `cac ruling canonize
   c012-e003-cache-key-format --message "Added lore cache-keys"` with a narrative
   of what changed. Otherwise ruling_note / `cac ruling note ... --message "..."`
   with a narrative of why no change is needed. Archive each dispositioned ruling
   with ruling_archive; rulings are never deleted.
   Archive the campaign only when it
   is terminal, integrated and every encounter is terminal. campaign_archive /
   `cac campaign archive c012` archives its encounters and current bosses; released
   bosses owned by later attempts remain untouched, and rumors and rulings are never
   touched by campaign archiving. Standalone
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
