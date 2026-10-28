---
name: world-planner
description: Plan and refine project goals, adopt an existing roadmap, assess boss readiness and dependencies, and distill campaign discoveries before tactical campaign selection.
---

# World Planner

Own goals and planning context. Use world-manager for static world/lore/regions
and its disclosure ladder; hand tactical selection/execution to campaign-manager.
Use the connected crypts-and-commits MCP tools first, cac CLI only when unavailable.
Managed records are MCP/CLI-only; never inspect or edit their files directly.
Missing bootstrap or stale search requires developer action: never run bootstrap
or index rebuild, suspend guardrails, or edit deployed skills.

## Start with context

For worked Git examples, read docs_get("branching-guide") /
cac docs get branching-guide. For adoption from older installations and targeted
local instruction updates, use docs_get("migration-guide") /
cac docs get migration-guide; workflow remains the procedural authority.

Orient with prime_get / cac prime get and effective planning_branch /
merge_target_branch. Follow docs_get("workflow") / cac docs get workflow,
especially "Agent planning and campaign workflow", for the canonical branch,
numbering and collision procedure. Branch names are configuration, not proof
of branch existence/integration. Inspect current branch/worktree, explain
detached/unrelated/dirty state, and reconcile without silent switches/overwrites.
Synchronize accepted merge-target history into planning under the project's
Git policy before boss edits or relying on assignments/prerequisites. Refresh
authorized remote refs best effort; disclose offline/incomplete observations.
Skill invocation supplies no permission to push, merge, publish, delete branches,
or message others; use existing user authorization without repeated approvals.

Prime exposes active_boss_names, active_bosses and active_boss_diagnostics for
actual active membership, not the entire roadmap. Hydrate relevant bodies and
diagnostics; do not select a first boss or treat damaged context as bossless.
Use all pages of boss_list(include_archived=True) / cac boss list --include-archived
before allocating numeric max+1 (001..999, then 1000); never recycle retained IDs.
Legacy names remain valid; ambiguous short refs need canonical names. Git branch
discovery is best effort, not an atomic allocator.

## Capture, refine, and recommend

| Intent | MCP | CLI fallback |
| --- | --- | --- |
| Read goal | boss_get(name) | cac boss get NAME |
| Inventory retained goals | boss_list(cursor,include_archived=True) | cac boss list --include-archived --cursor TOKEN |
| Capture goal | boss_create(name,body,summary) | cac boss create NAME --summary TEXT --body-file PATH |
| Refine | boss_update(name,body,summary) | cac boss update NAME --summary TEXT --body-file PATH |
| Read candidates | boss_candidates(cursor) | cac boss candidates --cursor TOKEN |
| Ready/withdraw/reactivate | boss_make_available / boss_withdraw / boss_reactivate | cac boss make-available / withdraw / reactivate NAME |
| Add/remove prerequisite | boss_assign_dependency / boss_unassign_dependency | cac boss assign-dependency / unassign-dependency NAME DEPENDENCY |
| Archive permitted goal | boss_archive(name) | cac boss archive NAME |

Omit cursor on the first page; finish next_cursor pages. MCP takes body strings,
not paths; CLI supports --body or --body-file (exclusive), or its editor.
Capture the goal, rationale, observable success conditions and unresolved choices;
body/summary travel together, summary at most 500 characters. Use existing
authorization, asking only for material missing meaning or decisions. Goal notes
do not require encounter-style independent review. Read full lore bodies when
needed; summaries route and never replace governing rules.

Candidates explain local eligibility, not business priority, integration proof,
or permission to select/open. Proposed is not_ready; available can be blocked;
assigned, withdrawn, vanquished and archived roots are excluded. Explain
prerequisite names/state/diagnostics, hydrate omitted details with boss_get, and
present a reasoned recommendation for developer choice. Local vanquished state
on an unmerged branch does not prove integrated implementation.

Scope/dependency edits leave an available goal available. Reassess readiness and
affected dependents with the developer; core does not reset it. To split an
oversized unassigned goal, create smaller goals and refine the original without
reusing/renaming its identity. Reconcile dependencies explicitly, never redirect
them automatically. Assigned and archived designs are frozen; record follow-up
ideas as rumors instead. Eligibility does not certify adequate design.

## Adopt existing roadmap context

Use boss_record(name,body,summary,progress,source,message,completed_on=None,
depends_on=None) / cac boss record NAME --progress VALUE --source TEXT
--message TEXT --summary TEXT --body-file PATH [--completed-on YYYY-MM-DD]
[--depends-on REF ...]. Repeat --depends-on for each existing prerequisite.

- planned/in_progress records start proposed. Original progress is an immutable
  provenance snapshot, not current readiness or CAC ownership. Make available
  only after the explicit readiness decision.
- completed records start unassigned vanquished, with nonblank source and
  message describing supplied outcome/evidence; unknown completed_on stays null.
  The optional date must be valid/nonfuture in UTC and is forbidden for other
  progress. CAC audits mean recording now, never backdated history.
- Enter prerequisite records first; source URLs/issue IDs are context, not
  inferred graph edges. Record incrementally, not a mandatory whole-roadmap
  import. Repeated live/archived names fail instead of upserting.
- External completion satisfies intact dependencies live or archived, without
  fabricated campaigns/encounters or a claim of independent verification/merge.
  Completed content is frozen. No undo/edit/restore workaround; mistakes require
  deliberate developer repair, never assistant filesystem edits.
- Existing campaign references are informational. Adopting ownership into an
  already-open legacy campaign is deferred; capture never bypasses draft locks.

## Rumors, archival, and handoff

After integrating campaign work and synchronizing planning, use rumors_list
/ cac rumors list, then rumors_get(campaign,cursor) / cac rumors get --campaign REF
[--cursor TOKEN]. Distill selected discoveries into approved new/refined goals;
do not force categories/lineage, expand old campaign scope, edit assigned goals,
or delete rumors automatically. If explicitly requested, rumors_delete(campaign)
/ cac rumors delete --campaign REF is supported; CLI deletion may prompt.

Planning's narrow campaign operation is archive: campaign_archive(name) /
cac campaign archive NAME only after integrated completed/abandoned history and
every encounter terminal. Current bosses move; released historical bosses and
rumors do not. Standalone boss_archive permits unassigned withdrawn or valid
external-completed goals, not arbitrary unassigned vanquished records.

Hand campaign-manager the chosen canonical goals, success conditions, eligibility
and unresolved integration limits. Selection uses deliberate tactics on an
assignment branch, not a copy of these notes; it neither opens a campaign nor
authorizes encounters. Bossless campaigns remain possible. Follow workflow's
manual reconciliation examples for legacy open work/rejected registration rather
than inventing repair APIs. Bootstrap redeployment is developer-only, separate
from authoring or record migration.
