# Crypts and Commits Workflow Reference Guide

## Purpose

### Crypts and Commits

Crypts and Commits ("CAC") preserves coding-assistant context and work history
across sessions in `.sourcebook/`. The developer is Game Master, setting context
and retaining final authority; assistants use CAC's MCP server or CLI to act on it.

### This document

Shared source of truth for record structures, lifecycles, relationships, and
agent procedures; update with observable changes. Skills follow this spec.
Retrieve via docs_get("workflow") / cac docs get workflow. MCP is primary;
CLI is the fallback/human interface, with parity except developer maintenance.

## CLI body input

Every CLI --body/-b operation also accepts --body-file PATH, including boss record.
The options conflict even for empty strings. Files are read as UTF-8 with newlines
preserved, then normal core validation/normalization/guards apply. Empty files give
empty bodies; sources are untouched. Relative paths use caller cwd, not project root.
Missing/unreadable/directory/invalid-UTF-8/conflicting input fails before writes.
File input never opens an editor; absent options retain editor/template behavior,
including encounter kinds. MCP takes body strings, never paths. Budgets and literal
rendering are unchanged. Example: cac campaign create goal --body-file "notes/plan.md".

## Domain model at a glance

Six Markdown/YAML record types live under the managed sourcebook:

| Type | Scope | Lifecycle |
| --- | --- | --- |
| World | Singleton | None |
| Lore | Many | Enabled/disabled |
| Region | Many | None |
| Boss | Project goals | proposed/available/withdrawn/vanquished |
| Campaign | Initiatives; one open per checkout | draft/open/paused/completed/abandoned |
| Encounter | Within a campaign | draft/reviewed/open/completed/abandoned |

Rumors are plain Markdown, at most one document per campaign, without frontmatter/lifecycle.

World/lore assignments are reciprocal: world.assigned_lore and lore.assigned_to_world.
Region/lore assignments are reciprocal: region.assigned_lore and lore.assigned_regions.
A lore entry can serve multiple regions. Enabled applicable lore is the union of
world-assigned lore and every assigned region's lore; this is resolved, not stored
on the encounter. Lore summaries route; full bodies govern review.

Campaigns contain encounters. Each encounter's regions list is one-directional;
regions store no encounter back-reference. Region assignment is draft-only and
at least one region is required for review. Encounter depends_on stores direct
prerequisites in the same campaign, on the dependent only. Reverse dependents are
computed for deletion checks. Dependency edits are draft-only; self/cycle and new
abandoned-prerequisite assignments fail. Boss dependencies and reciprocal campaign
membership are described below. No relationship implies permission to bypass a lifecycle.

## World

Singleton project orientation, read first. Free Markdown body, no status.
Frontmatter: name, assigned_lore, schema_version, common audit stamps.
Lore linkage is reciprocal as above.

| Operation | MCP | CLI |
| --- | --- | --- |
| Read | world_get | cac world get |
| Set attribute | world_set | cac world set |
| Replace body | world_set_body | cac world set-body |
| Assign/unassign lore | lore_assign_world / lore_unassign_world | cac lore assign-world / unassign-world |

### Branch settings

| Attribute | Effective default | Guidance |
| --- | --- | --- |
| merge_target_branch | main | Integration target |
| planning_branch | planning | Goals, rumors, archival |

Core/CLI/MCP world reads and prime expose effective metadata. New worlds persist
defaults; absent older keys default only in returned data. Reads and unrelated
writes never backfill them or change audit stamps. World-returning setters and
lore-link operations expose the same effective values. Explicit stored values,
even empty/malformed historical ones, are preserved; defaults depend on absence,
not truthiness. Ask for reconciliation of unusable configuration.

Persist an override with world_set(key="planning_branch",value="plans/team") /
cac world set planning_branch plans/team, or merge_target_branch similarly.
Only that attribute and audit updates persist. The generic setter accepts strings
without Git-name validation. Settings neither prove branch existence nor add
branch-dependent endpoints. These additive fields retain schema 1.

### Sourcebook schema versioning

Developer bootstrap stamps new world.md with the installed schema version.
Missing historical schema_version means 1. Existing bootstrap compares versions,
reporting behind/ahead without rewriting the stored version. Ahead means upgrade
the library; behind routes to world-manager and docs_get("migration-guide") /
cac docs get migration-guide. The guide states the current version and applicable
upgrade steps; there is no migration tool. Follow its explicit approval, capture,
temporary guardrail suspension, unconditional restoration, and verification
procedure before world_set("schema_version",...). Never infer that bootstrap
migrates records or suspend guardrails without approval.

## Lore

A standard, convention, or best practice checked against an encounter's Plan
before that encounter moves from `draft` to `reviewed`. World-assigned lore
applies globally, to every encounter; region-assigned lore only applies to
encounters assigned to that region.

- **Frontmatter**: `name`, `enabled` (bool), `assigned_to_world` (bool),
  `assigned_regions` (list), `summary` (routing summary, max 500 characters,
  required alongside every body write), plus the common stamps.
- **Body**: the governing rule text - the authoritative content a plan is
  checked against. The `summary` is a routing signal only, never a
  substitute for it.
- **Status**: not a guarded lifecycle - just an `enabled`/`disabled` flag that
  can be toggled at any time. Disabled lore is skipped when resolving the
  applicable set for an encounter.
- **Connections**: `assigned_to_world` <-> world's `assigned_lore`;
  `assigned_regions` <-> each listed region's `assigned_lore`.

| Operation | MCP tool | CLI fallback |
|---|---|---|
| Read | `lore_get` | `cac lore get` |
| List | `lore_list` | `cac lore list` |
| Create | `lore_create` | `cac lore create` |
| Replace body (+ summary) | `lore_update` | `cac lore update` |
| Set summary only | `lore_set_summary` | `cac lore set-summary` |
| Delete | `lore_delete` | `cac lore delete` |
| Enable / disable | `lore_enable` / `lore_disable` | `cac lore enable` / `disable` |
| Assign/unassign world | `lore_assign_world` / `lore_unassign_world` | `cac lore assign-world` / `unassign-world` |
| Assign/unassign region | `lore_assign_region` / `lore_unassign_region` | `cac lore assign-region` / `unassign-region` |

## Region

A documented path within the repository that needs its own conventions,
tech stack, or tooling described (e.g. "frontend" vs. "backend" in a web
app), and that lore can be scoped to.

- **Frontmatter**: `name`, `path` (the repository path this region covers -
  **not validated against the filesystem**; regions may be aspirational),
  `assigned_lore` (list), `summary` (routing summary, same required-alongside-
  body rule as lore), plus the common stamps.
- **Body**: free-form documentation of the region.
- **Status**: none.
- **Connections**: `assigned_lore` <-> each listed lore entry's
  `assigned_regions`. Regions have no stored link to the encounters assigned
  to them - that link lives only on the encounter side (see below).

| Operation | MCP tool | CLI fallback |
|---|---|---|
| Read | `region_get` | `cac region get` |
| List | `region_list` | `cac region list` |
| Create | `region_create` | `cac region create` |
| Replace body (+ summary) | `region_update` | `cac region update` |
| Set summary only | `region_set_summary` | `cac region set-summary` |
| Set path | `region_set_path` | `cac region set-path` |
| Delete | `region_delete` | `cac region delete` |
| Assign/unassign lore | (via lore's tools, above - region is the "target" object) | `cac lore assign-region` / `unassign-region` |

## Campaign

A long-running initiative, analogous to a Jira Epic (e.g. "Create the MVP"),
expected to span many encounters before completion.

- **Frontmatter**: `name`, `status`, canonical `bosses` list (empty for bossless), `archived` (bool, default `false`), plus common stamps.
- **Body**: free-form description of the initiative. Once a campaign reaches
  completed/abandoned status, a dated, attributed **postmortem log entry** is appended
  to the body and the body is locked (`campaign_update`/`cac campaign update`
  will fail while closed; explicit reactivation can reopen completed campaigns).
- **Status lifecycle**:

  | From | To | Trigger | Notes |
  |---|---|---|---|
  | `draft` | `open` | `campaign_open` | Only one campaign may be `open` at a time; fails naming the other open campaign otherwise. |
  | `draft` | `abandoned` | `campaign_abandon` | Message (postmortem) required. |
  | `open` | `paused` | `campaign_pause` | Fails if the campaign has an `open` encounter. |
  | `open` | `completed` | `campaign_complete` | Fails if the campaign has an `open` encounter. Message (postmortem) required; locks the body. |
  | `open` | `abandoned` | `campaign_abandon` | Same open-encounter guard and required-message/locking behavior as `complete`. |
  | `paused` | `open` | `campaign_open` | Same only-one-open-campaign guard as `draft` -> `open`. |
  | `paused` | `completed` | `campaign_complete` | Same guard/message/locking as `open` -> `completed`. |
  | `paused` | `abandoned` | `campaign_abandon` | Same guard/message/locking as `open` -> `abandoned`. |
  | `completed` | `open` | `campaign_reactivate` | Unarchived only; nonblank reason and single-open guard required. Preserves closing history. |
  | `abandoned` | - | - | Terminal; no further transitions. |

  ```mermaid
  stateDiagram-v2
      [*] --> draft
      draft --> open : open
      draft --> abandoned : abandon
      open --> paused : pause
      open --> completed : complete
      open --> abandoned : abandon
      paused --> open : open
      paused --> completed : complete
      paused --> abandoned : abandon
      completed --> open : reactivate
      completed --> [*]
      abandoned --> [*]
  ```

- **Connections**: contains its encounters (by directory nesting); an
  encounter records its parent campaign's name on its own frontmatter.

### Archiving

`archived` is an orthogonal flag, not a status - archiving a campaign never
changes its `status`, and a `completed`/`abandoned` campaign stays exactly
that after archiving. It exists to move finished work out of the way of the
active `campaigns/`/`encounters/<campaign>/` directories, into
`.sourcebook/archive/`, once nothing about it is still in flight.

Guard, enforced by `campaign_archive`/`cac campaign archive`: the campaign's
`status` must already be `completed` or `abandoned`; it must not already be
archived; and **every** encounter under it must also be `completed` or
`abandoned` - a strictly broader check than `complete`/`pause`/`abandon`'s
own open-encounter guard, which only blocks on an `open` encounter and lets
`draft`/`reviewed` ones through. There is no separate encounter-level archive
operation - archiving a campaign archives every one of its encounters in the
same call, atomically, each getting `archived: true`. There is currently no
reverse (unarchive) operation.

On success, the campaign file moves from `.sourcebook/campaigns/<name>.md` to
`.sourcebook/archive/campaigns/<name>.md`, and each encounter file moves from
`.sourcebook/encounters/<campaign>/<name>.md` to
`.sourcebook/archive/encounters/<campaign>/<name>.md` - the same layout, one
level under `archive/`.

Get resolves live or archived identities. campaign_list/encounter_list default
to live storage; include_archived=True / --include-archived inventories retained
history. encounter_order remains live-only. Archived reads never restore records.

Archiving does not remove a campaign/encounter from the search index - the
row for an archived object is updated in place (via the same `write_post`
call that moves the file), not deleted. It stays fully indexed, but
`index_search`/`cac index search` exclude archived content by default;
pass `include_archived=True`/`--include-archived` to include it alongside
live results. `index_status`/`cac index status` counts are unaffected by
this default - they still total archived and live content together, with
no live/archived split.

| Operation | MCP tool | CLI fallback |
|---|---|---|
| Read | `campaign_get` | `cac campaign get` |
| List name/status, optional archives | `campaign_list` | `cac campaign list [--include-archived]` |
| Create (starts `draft`) | `campaign_create` | `cac campaign create` |
| Replace body | `campaign_update` | `cac campaign update` |
| Delete (bossless only, no reverse claims) | `campaign_delete` | `cac campaign delete` |
| Open | `campaign_open` | `cac campaign open` |
| Pause | `campaign_pause` | `cac campaign pause` |
| Complete (+ postmortem message) | `campaign_complete` | `cac campaign complete` |
| Abandon (+ postmortem message) | `campaign_abandon` | `cac campaign abandon` |
| Archive (campaign + all its encounters) | `campaign_archive` | `cac campaign archive` |
| Reopen completed (+ reason) | `campaign_reactivate` | `cac campaign reactivate` |

## Encounter

A concrete unit of work within a campaign: a plan the agent is expected to
execute, with fixed body sections.

- **Frontmatter**: `name`, `campaign` (parent campaign name), `status`,
  `kind` (`scripted` or `unscripted`, default `scripted` - see "Kind: scripted
  vs. unscripted" below), `regions` (list), `depends_on` (list of direct
  prerequisite encounter names within the same campaign), `archived` (bool,
  default `false` - see the Campaign section's "Archiving" below; an
  encounter is never archived standalone, only as a cascade of its campaign
  being archived), plus the common stamps.
- **Body**: for a `scripted` encounter, four fixed sections - `Requirements`,
  `Rationale`, `Plan`, `Verification`; for an `unscripted` encounter, only
  `Requirements` and `Rationale` - plus, for either kind, an appended `Log`
  section once any transition or message carries a message. The fixed
  sections may only be *replaced* while status is `draft`; every later change
  is an append (via a transition's message, or `encounter_record_message`),
  never a rewrite.
- **Status lifecycle**: identical for both kinds.

  | From | To | Trigger | Notes |
  |---|---|---|---|
  | `draft` | `reviewed` | `encounter_review` | Message required. Requires at least one assigned region. Performed by an independent reviewer (see the `campaign-manager` skill), never the plan's author. Permanently locks the fixed sections (Requirements/Rationale, plus Plan/Verification for `scripted` kind). |
  | `draft` | `abandoned` | `encounter_abandon` | Message required. |
  | `reviewed` | `open` | `encounter_open` | Message optional. Fails, listing every unsatisfied prerequisite and its status, until all direct `depends_on` entries are `completed`. |
  | `reviewed` | `abandoned` | `encounter_abandon` | Message required. |
  | `open` | `completed` | `encounter_complete` | Message optional. |
  | `open` | `abandoned` | `encounter_abandon` | Message required. |
  | `completed` | - | - | Terminal; no further transitions. |
  | `abandoned` | - | - | Terminal; no further transitions. |

  ```mermaid
  stateDiagram-v2
      [*] --> draft
      draft --> reviewed : review
      draft --> abandoned : abandon
      reviewed --> open : open
      reviewed --> abandoned : abandon
      open --> completed : complete
      open --> abandoned : abandon
      completed --> [*]
      abandoned --> [*]
  ```

  `encounter_record_message` (no status change) is valid only while `reviewed`
  or `open`.

  Region assignment/unassignment and dependency assignment/unassignment are
  both only permitted while `draft`.

- **Connections**: belongs to one campaign (containment); `regions` list
  (one-directional, no back-reference on the region); `depends_on` list
  (one-directional storage within the same campaign; no self-dependency, no
  cycles, and an abandoned encounter cannot be a prerequisite).

### Kind: scripted vs. unscripted

`kind` is set once, at creation, and is not changed afterward - there is no
setter/assign operation for it.

- **`scripted`** (the default): a plan for future work. All four body
  sections apply; the reviewer checks the `Plan` against applicable lore
  before `draft` -> `reviewed`.
- **`unscripted`**: a record of manual work the developer or the agent
  already did outside the plan-first flow (direct edits, quick fixes,
  exploratory changes), captured after the fact so a later session can
  recover the intent behind it. Only `Requirements` (what was done) and
  `Rationale` (why) apply - there is no `Plan` or `Verification` to write,
  and their absence is not itself a defect. The status lifecycle, the
  independent-reviewer gate, and the three explicit user gates (see "Explicit
  user gates" below) are otherwise identical to a `scripted` encounter: the
  reviewer checks the recorded `Requirements`/`Rationale` against applicable
  lore in place of a `Plan`, giving the same after-the-fact lore check and
  follow-up opportunity that review provides for planned work.

| Operation | MCP tool | CLI fallback |
|---|---|---|
| Read | `encounter_get` | `cac encounter get` |
| List oldest-updated first, optional archives | `encounter_list` | `cac encounter list [--include-archived]` |
| Show in dependency order | `encounter_order` | `cac encounter order` |
| Create (starts `draft`; `kind` optional, defaults `scripted`) | `encounter_create` | `cac encounter create` |
| Replace body (only while `draft`) | `encounter_update` | `cac encounter update` |
| Delete (fails if depended on) | `encounter_delete` | `cac encounter delete` |
| Review (`draft` -> `reviewed`) | `encounter_review` | `cac encounter review` |
| Open (`reviewed` -> `open`) | `encounter_open` | `cac encounter open` |
| Record a message (no status change) | `encounter_record_message` | `cac encounter record-message` |
| Complete (`open` -> `completed`) | `encounter_complete` | `cac encounter complete` |
| Abandon | `encounter_abandon` | `cac encounter abandon` |
| Assign/unassign region | `encounter_assign_region` / `encounter_unassign_region` | `cac encounter assign-region` / `unassign-region` |
| Assign/unassign dependency | `encounter_assign_dependency` / `encounter_unassign_dependency` | `cac encounter assign-dependency` / `unassign-dependency` |

Every mutating encounter tool/command accepts an optional `campaign`
argument; when omitted, it defaults to the single currently `open` campaign
(failing if none is open). Read-only operations (`encounter_get`,
`encounter_list`, `encounter_order`) accept any existing campaign, including
a `completed`/`abandoned` one, so past work stays inspectable after the fact.

## Explicit user gates

Three points in the encounter lifecycle require the developer's explicit,
real-time approval before the agent proceeds. Reaching the status just before
each gate is never itself consent to cross it - the agent must stop and ask,
and wait for an explicit answer, every time the gate is reached.

1. **Before spawning the independent reviewer** (the prerequisite for
   `draft` -> `reviewed`). Drafting an encounter is not approval to review
   it. This approval is asked fresh every time this point is reached -
   including a re-review after a `REJECT`/`NOT-REVIEWABLE` verdict and a
   follow-up `encounter_update` to the draft, not only on the first pass.
   Only on an explicit yes does the agent spawn a *fresh* reviewer subagent
   (never itself, never a context-sharing fork).
2. **Before opening the encounter** (`reviewed` -> `open`, via
   `encounter_open`). A separate approval from gate 1. A `PASS-WITH-NOTES`
   verdict auto-transitions the encounter to `reviewed` without pausing for
   approval of its own - that approval already happened at gate 1 - but
   moving from `reviewed` into `open` and beginning execution is its own ask.
3. **Before marking the encounter complete** (`open` -> `completed`, via
   `encounter_complete`). Once the encounter's own Verification steps pass,
   the agent confirms with the developer before closing it out - never
   unilaterally, even when every check is green.

Each of these three gates must be written explicitly into the skill that
carries the encounter lifecycle - `campaign_manager`, under both
`templates/skills/claude/campaign_manager/SKILL.md` and
`templates/skills/codex/campaign_manager/SKILL.md` - not left implicit, and
not treated as adequately covered by a cross-reference to this document.
"Explicit" means the stop-and-ask instruction for each gate is present in the
skill's own wording, in a form an agent following the skill text alone (with
no memory of this guide) would still stop and ask. This requirement is not a
one-time authoring checklist item - it must hold every time either skill
template is modified or regenerated, for any reason, including a rewrite that
touches unrelated parts of the encounter lifecycle procedure. An edit to
either template that drops, waters down, or fails to carry forward any of the
three gates' stop-and-ask wording is a defect in that edit, to be caught the
same way any other lore violation is: by checking the skill template's actual
current text against this section, not by assuming a past edit is still
intact.

What is *not* separately gated: the draft -> reviewed transition itself, once
a `PASS-WITH-NOTES` verdict is in hand - it runs immediately, because gate 1
already covers it. Campaign-level transitions (`open`/`pause`/`complete`/
`abandon`/`archive`) and lore/region/world edits have no codified approval
gate of their own in this model; they take effect as soon as the
corresponding mutating tool is called.

## Codex encounter handoffs

The Codex `campaign-manager` skill makes two decision points explicit in
conversation. These handoffs supplement the encounter record and preserve
all three approval gates above. This guidance targets the Codex skill;
Claude's existing skill procedure is unchanged.

Each handoff is a substantive report that stands on its own: the developer
should understand the work or review outcome and make the next decision
without opening the full encounter. Include its full reference for deeper
inspection. Use several developed paragraphs or grouped bullets, scaling
depth to complexity and uncertainty. Explain why details matter; listing
topic labels is insufficient. Avoid a fixed word count, terse synopsis,
padding, or pasting the encounter.

After drafting, before requesting independent review, explain:

- Encounter and campaign identity, kind, `draft` status, the problem and
  motivation, and intended behavior or outcome; use a before/after when helpful.
- Scope and boundaries, affected areas, main implementation steps, and
  significant choices or tradeoffs with their reasons.
- Dependencies, assumptions, risks, and unresolved decisions that affect
  readiness; say when there are no unresolved decisions.
- Verification approach, concrete success criteria, and known limits.

For an `unscripted` encounter, explain work already performed, its rationale,
available evidence, and remaining follow-up instead of inventing a future
Plan or Verification. After revising a rejected or non-reviewable draft,
explain changes actually made, why they address the findings, and concerns
still outstanding before requesting renewed review approval.

After every independent review, identify the encounter and explain:

- Verdict, review coverage and limits, including which standards or areas
  were checked. Do not imply unreported evidence or implementation verification
  from a plan review.
- Each material finding's evidence or reasoning and practical importance.
  Distinguish blockers, actionable notes, and flagged-but-unverified concerns;
  explicitly say when none exist. Group routine successful lore checks rather
  than reproducing an exhaustive checklist.
- Consequences for scope, approach, risks, verification, or readiness; proposed
  responses versus actions actually taken; remaining uncertainty and conditions.
- Resulting status and locking implications, a reasoned recommendation to
  proceed or revise tied to the findings, and the next approval needed.

Handle the verdict before delivering the report:

- **PASS-WITH-NOTES:** first auto-transition using the reviewer's proposed
  message, then give the report. State that the encounter is `reviewed`
  and its sections are locked. Explain whether notes can be handled under
  the plan or need follow-up recorded with `encounter_record_message`;
  locked sections cannot be replaced. Request separate approval to open.
- **REJECT / NOT-REVIEWABLE:** keep the encounter `draft`, explain the
  blockers or missing information and their impact, and recommend revision
  or clarification before a fresh review. After revising, distinguish
  changes actually made from outstanding concerns and request renewed
  approval to launch a fresh reviewer. Revision alone is not a passing
  review.

For unscripted reviews, describe the findings' impact on the recorded
work's accuracy and any follow-up needed, rather than presenting work
already done as future execution. The conversational report supplements the
independent reviewer's message recorded by `encounter_review`; never replace
or rewrite that message. Preserve the reviewer's meaning and distinguish
your own recommendations from its findings. A
recommendation never authorizes a reviewer, opening, or completion.

Illustrative reports (use actual identities, evidence, and full references;
adapt detail to the encounter instead of treating these as a length ceiling):

**Scripted draft:** "`c001/e010-expand-encounter-handoff-reporting` is a
scripted draft in `c001-boss-edition`. The earlier guidance explicitly asks
for brevity, leaving too little context to decide about review or execution.
This draft requires reports that explain the approach and reasoning as well
as the outcome. It changes the packaged Codex skill and matching workflow
guidance; authoring both together keeps the instructions consistent.

The plan replaces brevity limits, develops examples, and checks each review
outcome. Report depth will follow complexity rather than a word quota, so
simple encounters need no filler. Guide size is a known constraint: retrieval
tests must still return the complete guide under the existing budget. Manual
scenario checks will assess whether reports support a decision; existing
tests and Ruff check packaging, retrieval, and repository health. No design
decision remains unresolved. May I launch independent review?"

**Passing review with a note:** "`c001/e010` passed with notes; it is now
reviewed and its sections are locked. The reviewer checked the plan against
all applicable lore and named sources, finding no blockers or unverified
concerns. This establishes plan compliance, not completed implementation.

The actionable note is guide size: e005 encountered truncation, so expanded
examples could make the guide unavailable in full. The planned retrieval
check addresses that risk without increasing budgets. I recorded the
reviewer's message; the documentation edits and retrieval check remain to
be done. I recommend proceeding because the note fits the existing plan,
with full retrieval required before completion. May I open the encounter?"
With no actionable notes, explicitly say so and explain how review coverage
supports readiness while identifying any remaining implementation uncertainty.

**Rejection and revision:** "The reviewer rejected the draft because it
targets deployed skills, whose changes would be overwritten on bootstrap.
The encounter remains draft and editable. I recommend revision to target
packaged templates and leave deployment to the developer. I have now changed
those paths and added a template/deployment check; no other concerns remain.
These revisions address the finding but have not passed independent review.
May I launch a fresh reviewer for the revised encounter?"

**Unscripted, not reviewable:** "The reviewer could not identify the timeout
fix from this unscripted record, so cannot assess it against applicable lore.
The record remains draft. The gap concerns documentation of completed work;
it does not establish that the fix failed. I recommend naming the changed
component and recording the observed evidence before renewed review. No
clarification has been made yet; the exact change remains unresolved."
An unscripted draft report should likewise describe the actual change, why
it was made, supporting observations, and follow-up rather than future execution.

## Agent planning and campaign workflow

world-manager owns static context, lore/regions, disclosure and migration routing.
world-planner owns goal planning/adoption/readiness, dependencies, splitting,
integrated rumor distillation and planning-side archival. campaign-manager owns
tactical selection/registration, draft membership, encounters and execution.
Both provider variants implement this procedure; invocation is not blanket
permission for publication, merging, destructive cleanup, or external messages.
Use existing authorization without repeating approvals. Encounter review/open/
completion gates above remain distinct; ordinary goal notes get no encounter gates.

### Orient, plan, and allocate

Read prime and effective branch settings; its bosses are active membership, not
a whole roadmap. Finish inventory pages, hydrate relevant bodies and diagnostics.
Bootstrap/index rebuild are developer-only. Full-text search finds encounter text,
not allocation inventories or graph discovery.

Synchronize accepted merge-target history onto planning under project Git policy
before edits/selection. Check checkout/branch/dirty/detached state; reconcile
without silent switches or overwrites. Refresh authorized remote refs best effort
and disclose gaps. Local completion is not integration; roadmap completion is
supplied historical evidence, not proof of a CAC merge.

Allocate numeric max+1, padded to three digits below 1000, continuing at 1000.
Never reuse retained IDs or infer the maximum from lexical/time/search order.
Bosses: all boss_list(include_archived=True) pages on synchronized planning.
Campaigns: all campaign_list(include_archived=True) pages plus known local/remote
cNNN branches, including unpublished reservations. Encounters: all
encounter_list(campaign=...,include_archived=True) pages within the exact campaign.
Matching cNNN-slug and cNNN-slug-assignment reserve one allocation. Legacy names
remain valid; ambiguous shorthand requires canonical names. Core allocates nothing.

Capture/refine via boss operations; roadmap recording preserves its original
progress/source evidence and truthful audit dates. Planned/in_progress is proposed
until explicit make-available. Explain candidate blockers, not-ready and eligible
without treating order as business priority or selection permission. Scope edits
retain available status; reassess readiness and affected dependents. Split only
editable goals, retaining identity and explicitly reconciling dependencies; never
rewrite them automatically or edit assigned designs.

### Selection, branches, and collision checks

Craft tactics for every developer-selected eligible goal/success condition.
On cNNN-slug-assignment from synchronized merge target, use campaign_create with
bosses (single-goal convenience: boss_assign_campaign). Confirm reciprocal links
and rollback errors. Integrate registration under project PR/direct-merge policy
before execution. Selection opens nothing/creates no encounters. Bossless campaigns
may start directly on cNNN-slug with the same allocation checks.

Create/resume cNNN-slug from accepted registration/merge target; if based on
assignment, reconcile registration first. Explicitly approved opening is on
execution; main/planning have no open campaign, paused work stays on execution.
These are guidance, not endpoint gates or mandatory CI/hosting. Honor custom
settings. Draft membership changes need campaign_set_bosses and a reason;
opening/reopening locks it. Boss designs stay frozen.

Check collisions at creation, after pull/merge/rebase integration, and before
completion for implementation integration; repeat after review fixes. Check
numeric IDs/names, same-campaign encounter IDs and reciprocal ownership of every
boss. A clean Git merge does not detect same-number/different-slug or competing
assignments. Explain conflicts and coordinate explicit repair; never silently
renumber, delete, force/reset, or edit managed files directly.

Complete only after selected goals/encounters are verified, with required
postmortem and user authorization. Group completion vanquishes all; abandonment
releases all current links while preserving historical membership. For pre-merge
review fixes, reactivate with reason on execution, retain membership/history,
do reviewed follow-up encounters, verify and recomplete. Post-merge new scope
needs new planning. Integrate terminal execution records before planning trusts
their outcomes. Publishing/merging requires applicable user authorization.

### Reconciliation and planning handoff

Rejected registration: check integration/branches; revise or explicitly abandon,
preserve notes/reservations. Never publish rejection as acceptance or auto-delete.
Accepted draft cancelled before execution: abandon with reason on execution,
integrate cleanup and synchronize planning; do not release links by hand.

Legacy unnumbered open work: inspect encounters/instructions, agree branch/name
reconciliation. Finish/abandon open encounters before pausing/closing. Preserve
history; no invented boss, bulk rename, or new endpoint branch gate.

Capture execution discoveries in one rumors document through CAC. Distill only
integrated rumors on planning into developer-selected goals/refinements; no forced
categories/lineage, implicit scope expansion, assigned-design edits or automatic
deletion. After synchronization, world-planner may archive integrated terminal
campaigns with all encounters terminal; only current bosses move, released history
and rumors stay untouched. Standalone archive follows withdrawn/external-completed
guards. No restore or assistant direct-file repair.

## Boss planning records

Bosses capture goals at `.sourcebook/bosses/<name>.md`, archived under
`.sourcebook/archive/bosses/`. Reserved `bosses/rumors/` is excluded from boss discovery/indexing.

Frontmatter contains `name`, required `summary` (maximum 500 characters),
`status`, `archived`, `depends_on` (direct canonical names), optional
`campaign`, optional adoption `provenance`, and common audit stamps. Ordinary
creation sets proposed, unarchived, no campaign, empty dependencies. Optional body
headings: Goal, Rationale, Success Criteria, Design Notes, Open Questions.
Body text cannot set frontmatter or bypass guards.

| Operation | MCP tool | CLI command |
| --- | --- | --- |
| Capture body and summary | `boss_create` | `cac boss create NAME --summary TEXT` |
| Record existing roadmap goal | `boss_record` | `cac boss record NAME --progress VALUE --source TEXT --message TEXT --summary TEXT` |
| Read metadata, summary, bounded body | `boss_get` | `cac boss get NAME` |
| Page canonical names | `boss_list` | `cac boss list` |
| Replace body and summary together | `boss_update` | `cac boss update NAME --summary TEXT` |
| Mark proposed goal ready | `boss_make_available` | `cac boss make-available NAME` |
| Withdraw proposed/available goal | `boss_withdraw` | `cac boss withdraw NAME` |
| Return withdrawn goal to proposed | `boss_reactivate` | `cac boss reactivate NAME` |
| Archive withdrawn/external completed goal | `boss_archive` | `cac boss archive NAME` |
| Add direct prerequisite | `boss_assign_dependency` | `cac boss assign-dependency NAME DEPENDENCY` |
| Remove direct prerequisite | `boss_unassign_dependency` | `cac boss unassign-dependency NAME DEPENDENCY` |

Create/update/record require body and summary together: CLI `--body/-b`,
`--body-file`, or template/current-body editor; MCP requires explicit strings.
Output preserves literal Markdown. Lists return canonical names and next_cursor
with cursor paging, not priority. MCP get/mutation results contain metadata,
summary, body, and identity; bodies are bounded.

Body/summary/dependency edits require unarchived, unassigned proposed/available
status. Available edits retain available status. Make-available requires proposed
status; prerequisites need not be satisfied. Withdraw requires unassigned
proposed/available status and never changes campaigns or incoming dependencies.
Reactivate requires unarchived, unassigned withdrawn status. Linked and vanquished
records are frozen. Every archived mutation is rejected. State changes preserve
the design body.

Standalone archive requires unassigned withdrawn status, or vanquished with valid
completed roadmap provenance. It preserves status/provenance/body, updates audit
stamps, and moves the record with archived=true. Collisions fail; persistence
failures restore bytes/index evidence. Reads resolve archives; lists need
include_archived=True/--include-archived. Retained names cannot be reused;
live/archive ambiguity fails. No delete, rename, restore, or generic status setter.

Dependencies store canonical names; adding rejects self/duplicate edges,
unknown/withdrawn targets, malformed storage, ambiguity, and cycles before writes.
Existing edges survive withdrawal/archive. Explicit removal may repair damage
only if the resulting entire graph is valid. Dependents are never rewritten;
availability is not reset. Numbered and legacy names/short refs remain supported.

Schema stays 1. Missing storage is empty; reads never write; creation is lazy.
No inferred goals, bulk conversion, bootstrap migration, or existing record rewrite.
Pre-e014 libraries must not mutate roadmap records: they cannot validate provenance
or its completion/archive rules. Downgrade requires developer conversion.
Storage links/path/namespace collisions fail. Endpoints perform no Git/branch automation.

### Roadmap adoption

boss_record(name,body,summary,progress,source,message,completed_on=None,depends_on=None)
is create-only; repeated live/archived names fail without updates. Required progress:
planned/in_progress -> proposed; completed -> unassigned vanquished, without a
synthetic campaign/encounter. Ordinary boss_create remains proposed-only.
Required nonblank source describes the roadmap/evidence; message explains capture
and, for completion, the outcome/evidence. CAC records an assertion, not proof of
Git integration. No fetching, automatic extraction, or bulk upsert.

Immutable provenance contains kind=roadmap, progress, source, message, completed_on.
Progress is the original snapshot, never current readiness/ownership. Audit dates
mean recorded now. completed_on is an optional YYYY-MM-DD completion date, only
for completed progress; invalid/future dates (UTC) fail. Unknown stays null.
CLI adds --completed-on and repeated --depends-on; refs resolve existing goals,
including archives, before one atomic write. Record prerequisites first; unresolved
external relations stay in prose. Historical outcomes need not replay prerequisite
readiness; graph damage still prevents downstream trust.

Planned/in_progress goals need explicit make-available approval. Existing campaign
references are informational; adopting open legacy campaign ownership is deferred.
Draft-only membership locks remain. External completions satisfy dependencies,
including when archived; ordinary completed-content freezing applies. Mistakes need
documented developer repair, never assistant direct edits. No undo API here.
Recorded reads reserve provenance/identity before body truncation and boss_get
hydration refs; impossible metadata fails explicitly, preflighted before record/archive.
Failures roll back cohort bytes/rows/fingerprints, preserving unrelated drift.
Prime still includes only actual active membership. Search indexes summary/body.
For example, record delivered b001, then planned b002 depending on b001, then
in_progress b003. Preserve roadmap references/evidence and known completion dates;
no entire-roadmap import or invented execution history is required.

## Campaign rumors

Rumors preserve discoveries at `.sourcebook/bosses/rumors/<canonical-campaign-name>.md`:
one optional plain UTF-8 document per existing campaign, created lazily. Missing
storage lists as empty. There is no frontmatter parsing, audit metadata, status,
summary, required structure, review gate, or rumor number. All text, including
empty strings, YAML-looking delimiters, brackets, Unicode, and newlines, round-trips
exactly. Capture does not expand scope, create bosses, or require conversion/lineage.

| Operation | MCP tool | CLI command |
| --- | --- | --- |
| List | `rumors_list(cursor=None)` | `cac rumors list` |
| Read | `rumors_get(campaign=None, cursor=None)` | `cac rumors get` |
| Create | `rumors_create(body, campaign=None)` | `cac rumors create` |
| Replace | `rumors_update(body, campaign=None)` | `cac rumors update` |
| Delete | `rumors_delete(campaign=None)` | `cac rumors delete` |

CLI campaign is `--campaign/-c`; cursor is `--cursor`. Campaign accepts canonical
or legacy names, cNNN refs, or active fallback. Missing/ambiguous owners fail. Create rejects existing
documents; get/update/delete reject absent ones. CLI create/update use the shared
body/body-file resolver or an editor initialized with empty/current text. MCP
requires body, allowing empty text. CLI delete confirms unless `--yes/-y`; MCP
delete is unconditional. Unsafe names, storage links/junctions, and path/type
collisions fail before writes.

Both surfaces return identical compact JSON; CLI prints it literally. Mutations
return canonical `campaign` and campaign `identity`. Get adds raw `body` chunk,
`truncated`, `next_cursor`, and separate `notice`. Complete reads have false
truncation and null cursor/notice. For a `TRUNCATED` response, pass `next_cursor`
as `cursor`/`--cursor` with the same campaign until null; concatenate only body
fields. Digest/character-offset cursors reject malformed, out-of-range, or stale
values; restart after edits. No direct-file-read fallback. The serialized envelope,
including escaped text, fits the shared response budget or fails if too small.
Other domains' get behavior is unchanged.

List returns bounded `{items, next_cursor}` in filename order with shared cursor
semantics. Items contain `campaign`, `identity`, and `diagnostic`; archived owners
are included. Missing owners yield null identity and an orphan diagnostic requiring
history reconciliation. Rumors never count/resolve as bosses, reserve boss numbers,
or affect candidates/dependencies. Rumors are excluded from index freshness checks.

All document operations allow terminal and archived owners; campaign/boss guards
remain intact. Completion, abandonment, reactivation, and archival leave rumors'
bytes and live path unchanged. No rumor archiving or automatic cleanup.

Execution edits/integrates its own rumors; planning distills, retains, or deletes
integrated notes. Assigned bosses stay frozen; Git retains history. Endpoints
never inspect Git or enforce branches.

### Candidate discovery

boss_candidates(cursor=None) / cac boss candidates --cursor TOKEN returns read-only
compact JSON, not proof of integration. Numeric names sort by integer then name;
legacy names follow lexically. Ties stay distinct; order is not priority.

Pool: live unassigned proposed/available goals. Proposed is not_ready; available is
eligible only with vanquished direct prerequisites and an intact reachable graph,
otherwise blocked. Archived completion counts. Other roots are excluded; readiness
is unchanged. Links must resolve, reciprocate, and match lifecycle/archive state:
available with draft/open/paused, vanquished with completed. Campaign status is shown.

Page: items, next_cursor, counts, healthy, diagnostics, diagnostics_omitted,
diagnostics_ref. Global counts: total_live, total_archived, pool, eligible, blocked,
not_ready, excluded, invalid (unreadable live records). Archived defects affect
health. Healthy means no diagnostics; unrelated damage does not hide healthy choices.
Unsafe/ambiguous storage fails. Counts distinguish empty, excluded, unready, blocked.

Items carry name, summary, status, classification, eligible, reason_codes,
prerequisite_count, unsatisfied_count, diagnostic_count, prerequisites,
diagnostics, and ref: boss_get. Prerequisite details carry name, status, archived,
satisfied, and optional campaign/campaign_status. Top reason codes: not_ready,
prerequisite_unsatisfied, integrity_error. Diagnostic codes: invalid_record,
invalid_summary, invalid_dependencies, duplicate_dependency, self_dependency,
missing_prerequisite, dependency_cycle, dependency_integrity, invalid_campaign_link,
campaign_not_found, ambiguous_campaign, invalid_campaign_record,
campaign_boss_mismatch, campaign_state_mismatch. Entries carry name/code/message
and optional prerequisite/campaign names. Reachable defects block dependents;
cycle diagnostics do not imply cycle membership.

Recorded items add roadmap {recorded_progress,source,source_truncated,ref:boss_get};
source is a bounded preview. External completed prerequisites add
completion_origin:roadmap and ref:boss_get; this never implies campaign ownership.

Whole-page compact JSON fits the shared budget: at most 16 details per list,
global diagnostics at most one quarter, reduced further if needed. Cuts report
prerequisites_omitted/diagnostics_omitted/summary_truncated; counts/eligibility stay
intact. Hydrate via boss_get/campaign_get; diagnostics_ref:boss_list routes omitted
issues. No bodies. Unfit required identifiers/fields fail explicitly. Cursors assume
an unchanged store, without snapshots.

### Promotion and campaign coupling

Campaigns have zero or more `bosses`; bosses have one current `campaign` at most.
Canonical lists sort numerically then legacy names, not by priority. Legacy `boss`
reads as singleton, absent/null as empty; dual/malformed/duplicate fields fail.
Reads never write; supported mutations normalize to `bosses`. Schema stays 1;
no bulk migration/bootstrap or primary alias. Older one-boss libraries cannot
operate on plural records; see migration-guide.

`campaign_create(name,body,bosses=None)` / `cac campaign create NAME --boss REF`
accepts repeated bosses; omitted/empty means bossless. New names remain literal,
unused live/archive, and unclaimed. Body-file/editor behavior is unchanged.
Selection atomically creates draft/links, leaves bosses available but frozen,
and opens no campaign/encounters. Additions require eligible, unassigned,
unarchived available bosses; co-selection never satisfies incomplete prerequisites.

`campaign_set_bosses(name,bosses,message)` / `cac campaign set-bosses NAME
--boss REF --message REASON` replaces the complete set only on unarchived drafts.
Repeat --boss; omit (MCP []) to clear. Require nonblank reason; resolve refs and
reject alias duplicates. Retained members reciprocate; removals release only this
campaign's links. Changes log old/new names and reason once; body updates preserve
that Log. Same-set retries are read-only regardless of order. Membership locks
after draft, including reactivation; body edits cannot change links.

Single-boss `boss_assign_campaign(name,campaign_name,body)` retains body/file/editor
input and boss/campaign/status/reused/boss_identity/campaign_identity/identity
output. Consistent retries are read-only after progress/archive and in groups;
ignore retry body, never shrink membership. Different/released targets fail.
Initial selection checks full eligibility; retries do not recheck prerequisites.

Completion records its postmortem and vanquishes all linked bosses. Abandonment
releases all current links, retaining the historical campaign list. Reactivation
requires unarchived completion, nonblank reason, and no other open campaign; it
returns every linked boss to available but assigned/frozen. Prior Log and closed
encounters remain; recompletion appends history. Bossless lifecycle still works.
Open/pause do not vanquish; existing encounter guards apply.

Completed archive moves all assigned bosses and terminal encounters, preserving
status and readable history. Abandoned archive never controls released bosses,
even if reassigned/archived/withdrawn/vanquished. Rumors stay live. Standalone boss
archive also accepts externally evidenced completion; no restoration/generic status setter.
Current/historical lists and reverse claims protect deletion. Broken/competing
ownership or lifecycle state blocks mutation without repair. Campaign reads expose
`bosses` and boss_link inspection; candidates diagnose malformed/orphan claims.

Preflight covers cohort/audits/paths/output. Changed boss metadata preserves design
bytes, summaries, dependencies and creation stamps. Exceptions restore affected
bytes/rows/fingerprints, including encounters, preserving unrelated records/drift.
RecoveryError identifies residual paths/rows. No automatic rebuild/retry, allocation,
Git check, crash journal or cross-process guarantee.


Campaign/encounter lists default to live records. include_archived=True /
--include-archived returns the scoped live/archive union with existing identities,
status fields, sorting and cursor budgets; ambiguous/unsafe storage fails. Archive
inventory is read-only and independent of search. Use all pages for retained IDs.

## Numbered references and canonical identity

Selectors accept `bNNN`, `cNNN`, `cNNN/eNNN`, and canonical names. Bare `eNNN`
needs an explicit/active campaign. Short refs use lowercase prefixes and at least
three ASCII digits with positive IDs; padding normalizes numerically, including
the 999/1000 transition. Canonical validation stays permissive; numbering/allocation
are conventions, not creation gates.

Resolution inventories live and archived records in the current project. A
numbered full name has prefix/digits/hyphen/nonempty slug. Numeric collisions,
including different padding or archived matches, raise ambiguity rather than
choosing a slug. Full slugged names and other exact legacy names remain inspection
routes. A historical literal name such as `b001` participates in the numeric
matches: it works alone but cannot shadow a colliding `b001-slug`. Duplicate
canonical files in live/archive are integrity errors even for full-name lookups.
Rumors do not participate. Malformed/unknown/wrong-domain refs fail before writes.

Qualification overrides active fallback; explicit campaign must resolve identically.
It bypasses no closed-campaign/frozen/lifecycle/archive guard. Encounter IDs and
prerequisite edges remain campaign-local.

### Operation/input matrix

| Surface | Reference inputs | Literal inputs |
| --- | --- | --- |
| Boss get/update/make-available/withdraw/reactivate/archive | existing name | body, summary |
| Boss assign/unassign-dependency | source name, prerequisite | missing canonical edge on explicit removal |
| Boss assign-campaign | existing boss | new campaign_name, body |
| Campaign get/update/delete/open/pause/complete/abandon/archive/reactivate | existing name | body, message |
| Campaign create / set-bosses | boss list refs; existing campaign for set | new create name, body, message |
| Encounter get/update/delete/review/open/record-message/complete/abandon | name, optional campaign | body, message |
| Encounter assign/unassign-region | name, optional campaign | region |
| Encounter assign/unassign-dependency | source, prerequisite, optional campaign | missing canonical edge on explicit removal |
| Encounter list/order, encounter create | existing campaign | new create name, body, kind, cursor |
| Boss/campaign create | none | new name, body, summary where applicable |
| Prime applicable-lore | encounter, optional campaign | returned lore refs unchanged |
| Boss/campaign lists and candidates | none | cursor, flags |

Lore/region/doc names, keys/values, messages, bodies, summaries, and search phrases
are literal. No resolver endpoint, boss deletion, or generic status setter exists.

Creation names stay literal; encounter create may select a campaign ref but not
create a qualified path. Dependencies canonicalize before graph checks/persistence;
mixed spellings cannot bypass self/duplicate/cycle guards. Explicit removal may
target a missing canonical edge; ambiguous shorthand cannot choose one. Reads
never reinterpret or rewrite stored links/graph names.

### Identity and budgets

MCP object get/mutation results add `identity` without replacing existing fields.
CLI target commands print an `identity:` JSON line. Identity contains `canonical`,
`short` (usable normalized ref or null), and `reason` (null when usable).
Encounter identities also contain canonical `campaign`; when a qualified ref is
usable they include contextual `bare_short`. An unavailable ref reports
`unnumbered`, `ambiguous`, `missing`, or `invalid_storage`; encounters may report
`campaign_unnumbered`/`campaign_ambiguous`/other parent reasons. Deleted results
retain canonical identity but use null short and reason `deleted`.

Boss/campaign/encounter paged lists retain original `items` and `next_cursor`,
adding parallel `identities` for that page only. Encounter order rows and candidate
items add identity. Applicable-lore keeps its lore-entry result shape.
Prime and search expose canonical stored names. Names in stored relationships remain
canonical, independently of identity display metadata.

List paging measures compact JSON for items plus identities and envelope before
selection, using shared cursor semantics. Candidate identities participate in
the existing whole-page bound before explanation truncation. Required identities
are never cut into different identifiers; if the minimum cannot fit, return an
explicit budget error. Oversized encounter order requires inspecting paged lists
instead of silently dropping rows. Get bodies reserve identity space before
truncation; normal metadata and literal markdown contracts remain intact.

CLI/MCP share references.select/inputs; lower storage routines consume exact names
without reinterpreting damaged links. Resolution may cache request-local inventory,
never persistent maps, writes, number reservations, branch/network lookups, or
migration. Schema stays 1; skills carry Git collision checks; deployment is separate.
The docs budget is 64,000 characters; ordinary response budgets are unchanged.

## Cross-cutting: priming, search, and docs

Auxiliary capabilities (not content types):

- **Prime** (prime_get / cac prime get) bundles world, enabled world-lore
  summaries, region map, active campaign/boss bodies. prime_applicable_lore /
  cac prime applicable-lore resolves enabled world union encounter-region lore.
- **Search index** (`index_status` / `cac index status`, `index_search` /
  `cac index search`) is a full-text index over `.sourcebook` content kept in
  sync automatically for world, lore, region, boss, campaign, and encounter records
  as content changes through `cac`. Rebuilding it
  (`cac index rebuild`) is developer-only and intentionally not exposed over
  MCP. `index_search` excludes archived campaigns/encounters/bosses by default -
  see the Campaign section's "Archiving" above for the `include_archived`
  opt-in and the counts-vs-search asymmetry.

Prime exposes `active_boss_names` (all declared names), `active_bosses` (validated
metadata/summary/body entries), and `active_boss_diagnostics` (code/campaign/boss/
message entries). Boss metadata includes name/status/archived/depends_on/campaign.
No active campaign or bossless means empty lists. Broken members remain named
with explicit diagnostics; group/storage errors may use boss=null. Singular
active_boss/active_boss_diagnostic are removed. No expansion, alias or repairs.

Core `prime.present` budgets the serialized bundle: reserve metadata/routing,
then divide remaining space by remaining bodies in world/campaign/boss order.
`truncations` is empty if all fit; each cut adds
`{field,notice:"TRUNCATED",ref:{tool,name?}}` with world_get/campaign_get/boss_get.
Unfit metadata fails; routing is never silently dropped. CLI renders the same
facts literally; in-process assembly retains full bodies.

Boss search indexes summary plus body with name/status/audit/archive metadata.
All statuses are searchable, not an eligibility assertion. Existing phrase,
filter, ranking, paging and snippet semantics remain. Oversized responses fail
with guidance to lower max_results/snippet_tokens; hits are not silently dropped.

Freshness compares identity, relative location, and SHA-256 of raw UTF-8 records
(metadata included) to a versioned SQLite manifest. Inventory covers world/lore/
region and live/archived boss/campaign/encounter records, including orphaned
encounters; excludes rumors, unrelated files, and cache. No Git/mtime inference.
Missing stays missing. Legacy/unsupported, divergent, unreadable, or invalid data
requires developer `cac index rebuild`; reads never write/migrate/rebuild.
Returning to the indexed source snapshot restores freshness.

Core search returns list-or-None or raises `StaleIndexError` before stale hits.
CLI exits nonzero without hits; MCP returns
`{built:true,stale:true,hits:[],diagnostic:{code:"stale_index",message,recovery}}`.
Normal/missing MCP results add stale=false to built/hits. Status adds freshness
(missing/fresh/stale) and nullable diagnostic to built/counts; stale counts are
snapshot counts. Demo's read-only core adapter reports unavailable/stale/no hits.

Writes atomically sync affected rows/fingerprints without blessing unrelated drift.
Archive changes that identity's location; source removal finishes before return.
Scoped rollback restores bytes/rows/fingerprints or reports incomplete recovery.
Rebuild publishes transactionally, never as automatic failure recovery. Guarantees
cover local operations, not concurrent writers/crashes. Index format is independent
of sourcebook schema.
- **Docs**: `docs_list` / `cac docs list` pages name/summary pairs;
  `docs_get(name)` / `cac docs get NAME` retrieves a packaged, read-only guide.
  `workflow` is authoritative; `branching-guide` supplies worked Git examples;
  `migration-guide` covers target-guide access from old installations, library
  upgrade, developer-run redeployment, targeted instruction edits and branch
  adoption separately from schema migration. Boss Edition retains schema 1;
  ordinary adoption suspends no guardrail. Preserve user-owned instruction
  imports/unrelated rules; bootstrap never rewrites them. Pull these references
  through world-manager's disclosure ladder rather than duplicating them locally.

## Example: an encounter's lifecycle, conversation to commit

1. Orient with prime_get and select the task's context. If no campaign fits,
   world-planner helps capture/choose goals; capture is not assignment.
2. With authorization, campaign-manager selects eligible goals, crafts a tactical
   draft and registers it on the assignment branch. A bossless campaign can skip
   registration. Reconcile registration and switch to its matching execution
   branch before explicitly approved opening; no campaign opens on planning/main.
3. Draft the encounter with Requirements/Rationale/Plan/Verification, assign
   regions and direct prerequisites. Unscripted work records only Requirements/
   Rationale. Deliver the substantive draft handoff before asking for review.
4. Obtain explicit independent-review approval. Spawn a fresh reviewer with no
   inherited context, using the template and only the two canonical identities.
   It reads the applicable lore bodies itself.
5. PASS-WITH-NOTES: main thread immediately records the reviewer's message through
   encounter_review and reports findings; fixed sections lock. REJECT or
   NOT-REVIEWABLE: revise while draft and obtain fresh approval before re-review.
6. Obtain separate opening approval; encounter_open requires every dependency
   completed. A passing plan review supplies no execution authorization.
7. Execute the Plan. Log deviations with encounter_record_message while reviewed/
   open; do not replace locked sections.
8. Run Verification (or confirm unscripted accuracy/follow-ups). After it passes,
   obtain developer completion confirmation, then encounter_complete.
9. When explicitly asked, commit deliverable and encounter record/log together.
   Git attribution preserves the decisions and implementation across sessions.
   Encounter completion does not authorize campaign completion, push, or merge;
   those follow the user's authorization and campaign workflow.

## Bootstrap (developer-only, not part of the ongoing workflow)

`cac bootstrap init` creates the `.sourcebook` directory and seeds
`world.md`, registers the MCP server, deploys the guardrails, and deploys the
agent skills into a target project. It is invoked by the developer only,
never by an agent, and is intentionally not exposed over MCP at all - it sits
outside the day-to-day domain model described above.

### Codex patch guard

The packaged Codex `PreToolUse` hook is registered for `^apply_patch$` only.
It checks the actual file-operation headers (`Add File`, `Update File`,
`Delete File`, and `Move to`) in the patch, denying the whole operation when
any target has a normalized `.sourcebook` path component. Both move endpoints
and every file in a multi-file patch are checked. Added, removed, and context
lines are not file headers, so ordinary repository patches can discuss
sourcebook paths without being blocked. Shell calls are not filtered by this
hook. The MCP/CLI-only instruction for managed content remains binding.

Supported events have `tool_name: "apply_patch"` and either a string
`tool_input` or an object whose `command` field contains the patch string.
Headers start at column zero, with standard LF or CRLF line endings and
unquoted file paths. The guard normalizes dot segments and slash/backslash
separators; Windows paths use case-insensitive component comparison, while
native POSIX paths retain case. Header scanning does not require a complete
patch envelope; apply_patch itself validates patch syntax. Invalid JSON,
missing/wrongly typed fields, unsupported payloads, and text without recognized
headers yield no hook decision. This lexical guard is not a complete filesystem
sandbox: symlink/junction aliases, unusual filesystem path aliases, and other
tool payload formats are outside its enforcement contract.

Developer-run bootstrap replaces the framework-owned deployed script and
upgrades recognized legacy `^(Bash|apply_patch)$` registrations. It retains one
apply_patch-only framework registration without duplicates, preserving unrelated
hooks (including those sharing the broad group), settings, and recognized hook
customizations. Custom hook commands or matchers outside the known framework
registration are left alone and may still need developer review. The developer
reviews/trusts the updated project hook through `/hooks` and re-enables it if
temporarily disabled. Agents neither redeploy the hook nor change live trust
settings. Local `CLAUDE.md`/`AGENTS.md` descriptions may need targeted adoption
edits after deployment; bootstrap does not rewrite those user-owned files.
