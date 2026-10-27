# Crypts and Commits Workflow Reference Guide

## Purpose

### Crypts and Commits

Crypts and Commits ("CAC") preserves coding-assistant context and work history
across sessions in `.sourcebook/`. The developer is Game Master, setting context
and retaining final authority; assistants use CAC's MCP server or CLI to act on it.

### This document

This is the shared source of truth for current record structures, lifecycles,
relationships, and agent procedures. Update it with observable model changes;
agent-specific skills follow this spec. Retrieve it using `docs_get("workflow")`
or `cac docs get workflow`. MCP is the primary agent interface; CLI is the fallback
and human interface. Both expose equivalent operations except developer maintenance.

## CLI body input

All CLI operations with `--body/-b` also accept `--body-file PATH`: world
`set-body`, and lore, region, boss, campaign, encounter, and rumors `create`/`update`.
These options are mutually exclusive, even when the inline body is empty.

The shared resolver reads UTF-8 with newlines preserved, then applies ordinary core
normalization, validation, summary requirements, and lifecycle guards. Input files
are untouched; empty files supply empty bodies. Without either option, existing
editor/template behavior applies, including encounter-kind templates. Missing,
unreadable, directory, invalid UTF-8, or conflicting input fails before writes.
Explicit file input never opens an editor. Paths are relative to the caller's cwd,
independently of project-root discovery.

Example: `cac campaign create opening-gambit --body-file "notes/campaign plan.md"`.
MCP receives body strings, never file paths; file input changes no domain operation,
response budget, or literal output rule.

## Domain model at a glance

Six record types, each stored as a markdown file with YAML frontmatter
under `.sourcebook/`:

| Type      | Cardinality           | Has a status lifecycle? |
|-----------|------------------------|--------------------------|
| World     | Singleton              | No                       |
| Lore      | Many                   | No (simple enabled/disabled flag, not a guarded lifecycle) |
| Region    | Many                   | No                       |
| Boss      | Many                   | Yes: proposed -> available -> withdrawn; reactivate -> proposed |
| Campaign  | Many (one active/`open` at a time) | Yes: `draft` -> `open` -> `paused`/`completed`/`abandoned` |
| Encounter | Many, nested under a campaign | Yes: `draft` -> `reviewed` -> `open` -> `completed`/`abandoned` |

Campaign rumors are an additional plain markdown document type: at most one per
campaign, with no frontmatter schema or lifecycle. See "Campaign rumors" below.

### How the types connect

```
World  <---- assign/unassign ---->  Lore  <---- assign/unassign ---->  Region
                                                                           ^
                                                                           |
                                                                      assign/unassign
                                                                           |
Campaign  ---- contains ---->  Encounter  ---- assigned to ---------------+
                                    ^  |
                                    |  +---- depends_on ---> Encounter (same campaign)
                                    +---------------------------------------+
```

- **World <-> Lore** (bidirectional): assigning lore to the world records the
  link on *both* sides - the world's `assigned_lore` list and the lore's
  `assigned_to_world` flag.
- **Region <-> Lore** (bidirectional): assigning lore to a region records the
  link on both sides - the region's `assigned_lore` list and the lore's
  `assigned_regions` list. A lore entry may be assigned to more than one
  region.
- **Campaign -> Encounter** (containment): an encounter always belongs to
  exactly one campaign; it is stored nested under that campaign.
- **Encounter -> Region** (one-directional): recorded only on the encounter's
  `regions` list. A region has no back-reference to the encounters assigned
  to it. Region assignment is only permitted while the encounter is `draft`,
  and at least one region must be assigned before `encounter_review` will
  succeed.
- **Encounter -> Encounter** (`depends_on`, one-directional storage): a direct
  prerequisite is recorded only on the *dependent* encounter's `depends_on`
  list, within the same campaign. The reverse ("what depends on me") is never
  stored - it's computed on demand (e.g. to block deleting an encounter other
  encounters still depend on). Dependency changes are only permitted while
  the dependent encounter is `draft`; self-dependencies and cycles are
  rejected, and an abandoned encounter cannot be assigned as a prerequisite.

Lore's effect on an encounter is resolved, not stored directly on the
encounter: the applicable set for a given encounter is world-assigned lore
*union* the lore assigned to every region that encounter is assigned to
(enabled entries only).

## World

The project-level summary: goals, purpose, and domain orientation. Read first
to prime context for any other work. Exactly one exists per project.

- **Frontmatter**: `name`, `assigned_lore` (list), `schema_version` (int -
  the `.sourcebook` domain model's format version; see "Sourcebook schema
  versioning" below), plus the common
  `created_by`/`created_on`/`updated_by`/`updated_on` stamps applied on every
  write.
- **Body**: free-form markdown summary.
- **Status**: none - the world is never in a lifecycle state.
- **Connections**: `assigned_lore` <-> each listed lore entry's
  `assigned_to_world` flag (see above).

| Operation | MCP tool | CLI fallback |
|---|---|---|
| Read | `world_get` | `cac world get` |
| Set a frontmatter attribute | `world_set` | `cac world set` |
| Replace the body | `world_set_body` | `cac world set-body` |
| Assign/unassign lore | (via lore's tools, below - world is the "target" object) | `cac lore assign-world` / `unassign-world` |

### Branch settings

The world supplies two configurable branch names:

| Attribute | Effective default | Intended use by branch-workflow guidance |
| --- | --- | --- |
| `merge_target_branch` | `main` | Integration target for campaign work |
| `planning_branch` | `planning` | Boss planning and rumor distillation |

World reads and the world portion of prime expose these fields in `metadata`
through core, CLI, and MCP. New worlds persist both defaults from the packaged
template. Older worlds need no migration: missing keys are filled in the
returned metadata only. Reads do not rewrite files or audit stamps, and
unrelated writes do not backfill missing defaults. World-returning setters,
body updates, and lore-link operations expose the same effective metadata.

Use the existing `cac world set merge_target_branch trunk` and
`cac world set planning_branch plans/team` commands to persist explicit
overrides, or `world_set(key="planning_branch", value="plans/team")` through MCP.
Only the explicitly set attribute is persisted along with normal audit updates;
the other setting still uses its default if absent. Explicit stored values are
preserved, including empty or malformed historical values: fallback depends on
key absence, not truthiness. The generic setter retains its string-value
contract and adds no branch-name validation policy. Configure meaningful Git
branch names; these values are configuration, not proof that a branch exists.

These optional fields do not change the sourcebook schema version. Endpoints
do not inspect, create, switch, or merge Git branches, and do not gate lifecycle
operations on these settings. They supply configuration for future branch
workflow guidance; this feature alone does not deploy that guidance or change
the current skill procedures.

### Sourcebook schema versioning

`schema_version` is stamped onto every `world.md` `cac bootstrap init`
creates from scratch, set to the format version the installed `cac` package
currently expects. A sourcebook created before this attribute existed has
none; a missing value is treated as version 1, the format that existed
before versioning was introduced.

`cac bootstrap init` compares an *existing* `world.md`'s `schema_version`
against the installed `cac`'s expected version whenever it runs against an
already-bootstrapped project, and reports if the sourcebook is behind (needs
migration) or ahead (the installed `cac` is older than the sourcebook and
should itself be upgraded). Bootstrap only reports this - it never edits
`schema_version` on an existing file.

Migrating a behind sourcebook to the current version is the coding
assistant's job, via the `world-manager` skill, guided by the `migration-guide`
doc (`docs_get("migration-guide")` / `cac docs get migration-guide` - see
"Cross-cutting: priming, search, and docs" below). That doc states the
current schema version, a generic procedure for temporarily suspending and
then restoring the project's `.sourcebook`-is-MCP/CLI-only guardrail (a real
migration is likely to need direct file edits the generic per-object setters
can't perform), and one `## Migrating from version N to N+1` section per
schema change. There is deliberately no separate migration tool - the agent
reads the guide and makes the changes itself, then records completion with
`world_set("schema_version", ...)`.

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

Read/list asymmetry: `campaign_get`/`cac campaign get` and
`encounter_get`/`cac encounter get` transparently resolve an archived
campaign/encounter (checking the live location, then the archive location),
so a single lookup by name keeps working unchanged after archiving.
`campaign_list`, `encounter_list`, and `encounter_order` do **not** - they
only ever look at the live directories, so an archived campaign disappears
from `campaign_list`, and calling `encounter_list`/`encounter_order` against
an archived campaign now returns an empty result. Archived content is
inspectable one item at a time via `_get`, not via bulk listing.

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
| List (name + status) | `campaign_list` | `cac campaign list` |
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
| List (oldest-updated first) | `encounter_list` | `cac encounter list` |
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

## Boss planning records

Bosses capture goals before campaign selection. Records live at
`.sourcebook/bosses/<name>.md`; archives at
`.sourcebook/archive/bosses/<name>.md`. The nested `bosses/rumors/` namespace
is reserved for campaign rumors and excluded from boss enumeration and indexing.

Frontmatter contains `name`, required `summary` (maximum 500 characters),
`status`, `archived`, `depends_on` (direct canonical names), optional
`campaign`, and the common creation/update stamps. Creation sets proposed,
unarchived, no campaign, and an empty dependency list. Suggested body headings
are Goal, Rationale, Success Criteria, Design Notes, and Open Questions;
none are required. Body text cannot set frontmatter or bypass guards.

| Operation | MCP tool | CLI command |
| --- | --- | --- |
| Capture body and summary | `boss_create` | `cac boss create NAME --summary TEXT` |
| Read metadata, summary, bounded body | `boss_get` | `cac boss get NAME` |
| Page canonical names | `boss_list` | `cac boss list` |
| Replace body and summary together | `boss_update` | `cac boss update NAME --summary TEXT` |
| Mark proposed goal ready | `boss_make_available` | `cac boss make-available NAME` |
| Withdraw proposed/available goal | `boss_withdraw` | `cac boss withdraw NAME` |
| Return withdrawn goal to proposed | `boss_reactivate` | `cac boss reactivate NAME` |
| Archive unassigned withdrawn goal | `boss_archive` | `cac boss archive NAME` |
| Add direct prerequisite | `boss_assign_dependency` | `cac boss assign-dependency NAME DEPENDENCY` |
| Remove direct prerequisite | `boss_unassign_dependency` | `cac boss unassign-dependency NAME DEPENDENCY` |

Create/update require body and summary together. CLI accepts `--body/-b`,
`--body-file`, or an editor initialized with template/current body when neither
body option is supplied. MCP requires explicit body and summary strings.
Both surfaces preserve literal markdown, page lists with `cursor`/`--cursor`,
and budget get bodies. MCP mutation results use the same bounded
`{metadata, summary, body}` shape as get. Lists return canonical names and a
next cursor; deterministic ordering does not express priority.

Body/summary/dependency edits require unarchived, unassigned proposed/available
status. Available edits retain available status. Make-available requires proposed
status; prerequisites need not be satisfied. Withdraw requires unassigned
proposed/available status and never changes campaigns or incoming dependencies.
Reactivate requires unarchived, unassigned withdrawn status. Linked and vanquished
records are frozen. Every archived mutation is rejected. State changes preserve
the design body.

Standalone archive accepts only unassigned withdrawn bosses, preserves status
and body, updates audit stamps, and moves the record while setting archived.
Destination collisions are rejected; persistence/move failures restore the live
record and remove the incomplete archive. Get and canonical resolution read live
and archived records. Default lists exclude archives; use `include_archived=True`
/ `--include-archived` to inventory retained allocations. Names cannot be reused.
Live/archive ambiguity is an error. There is no delete, rename, restoration,
arbitrary metadata setter, or public vanquish operation.

Dependencies persist full canonical names under existing permissive validation.
Numbered names are optional; short refs are supported as below; allocation is deferred. Adding edges
rejects self references, duplicates, unknown/withdrawn targets, and cycles.
Graph changes validate stored dependency types, missing references, live/archive
ambiguity, and cycles before writes. Existing edges to later-withdrawn bosses
remain visible, including after archival. Archived vanquished prerequisites
resolve normally. Explicit removal can repair missing references or break cycles
if the resulting entire graph is valid; unrelated damage still blocks changes.
Dependents are never rewritten, and changes do not reset availability.

Schema compatibility: this is additive storage within schema version 1. Missing
storage is empty in an existing bootstrapped project; reads create nothing and
first create provisions directories lazily. No existing world/campaign is
rewritten, no historical bosses are inferred, and no migration/bootstrap rerun
is needed. Upgrade the library to use these interfaces; older libraries do not
manage bosses. Storage links and namespace/path collisions are rejected rather
than followed outside record locations.

Vanquished is set by campaign completion; reads preserve optional campaign links.
Number allocation remains deferred. Boss endpoints perform no branch inspection,
switching, or merge automation; world settings do not change endpoint behavior.

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

`boss_candidates(cursor=None)` / `cac boss candidates --cursor TOKEN` return
read-only local-record discovery as compact JSON. They do not prove integration.
Numeric bNNN-slug names sort by integer, then name; legacy names follow lexically.
Numeric ties retain distinct names. Order is not priority.

The pool contains live, unassigned proposed/available goals. Proposed goals are
not_ready; available goals are eligible only when all direct prerequisites are
recorded vanquished and their reachable graph has no integrity defects; otherwise
they are blocked. Archived vanquished prerequisites still satisfy the status rule.
Assigned/withdrawn/vanquished/archived roots are excluded. Readiness is unchanged.
Optional campaign links must resolve, reciprocate the boss, and agree on state:
available with draft/open/paused; vanquished with completed. Linked campaign
statuses are reported, including abandoned/paused.

Page fields: items, next_cursor, counts, healthy, diagnostics,
diagnostics_omitted, diagnostics_ref. Counts are collection-wide before paging:
total_live, total_archived, pool, eligible, blocked, not_ready, excluded, invalid.
Invalid counts unreadable live records; archived defects affect health.
Counts distinguish empty storage, no pool, not-ready goals, and blocked work.
Healthy means no integrity diagnostics. Unrelated damage remains visible without
hiding healthy choices; unsafe/ambiguous storage raises a domain error.

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

Compact JSON for the whole page fits the shared response budget. Details and
diagnostics show at most 16 entries per list, reduced further as needed; global
diagnostics use at most one quarter of the budget. Fields prerequisites_omitted,
diagnostics_omitted, and summary_truncated disclose cuts; counts and eligibility
remain intact. Hydrate names with boss_get/campaign_get; collection
diagnostics_ref: boss_list routes omitted problems to inventory and reads.
Bodies are never included. If required fields/identifiers cannot fit, return an
explicit budget error. Cursors assume an unchanged store; no snapshot is saved.

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
archive still requires unassigned withdrawn status; no restoration/vanquish setter.
Current/historical lists and reverse claims protect deletion. Broken/competing
ownership or lifecycle state blocks mutation without repair. Campaign reads expose
`bosses` and boss_link inspection; candidates diagnose malformed/orphan claims.

Preflight covers cohort/audits/paths/output. Changed boss metadata preserves design
bytes, summaries, dependencies and creation stamps. Exceptions restore affected
bytes/rows/fingerprints, including encounters, preserving unrelated records/drift.
RecoveryError identifies residual paths/rows. No automatic rebuild/retry, allocation,
Git check, crash journal or cross-process guarantee.

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

The public core input boundary is `references.select` and its `inputs` adapter,
shared by CLI/MCP. Domain/storage routines below it deliberately consume exact
canonical names so damaged stored references cannot acquire new meaning. A
request-local inventory may be cached; no persistent map, index, file/audit write,
number reservation, branch/network lookup, or migration occurs during resolution.
Schema version stays 1. Planning/branching skill adoption and Git collision checks
remain later work. The dedicated docs budget is 64,000 characters so this full
canonical reference remains retrievable; ordinary response budgets are unchanged.

## Cross-cutting: priming, search, and docs

Three auxiliary capabilities sit on top of the six content types above -
none of them is a content type itself:

- **Prime** (`prime_get` / `cac prime get`, `prime_applicable_lore` /
  `cac prime applicable-lore`) assembles cross-object context in one call
  instead of chaining individual reads: the world, world-assigned enabled
  lore summaries, the region map, and active campaign and boss bodies in one
  round trip; and, for a specific encounter, the exact enabled lore set that
  applies to it (world-assigned union its assigned regions' lore).
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
- **Docs** (`docs_list` / `cac docs list`, `docs_get` / `cac docs get`) is a
  small, read-only set of reference guides packaged with `cac` itself -
  framework-owned, not `.sourcebook` content, and not user-editable. `docs_list`
  returns `name` + `summary` pairs (paged, same routing-signal pattern as
  lore/region); `docs_get(name)` returns one doc's full body (e.g.
  `docs_get("workflow")` for this guide, or `docs_get("migration-guide")` for
  the sourcebook schema migration procedure - see "Sourcebook schema
  versioning" above). It exists so a consuming project's `CLAUDE.md`/`AGENTS.md`
  doesn't need to carry deep CAC procedural detail inline - an agent session
  pulls a doc in only when a task actually needs it, via the `world-manager`
  skill's disclosure ladder (its fourth, "go deeper" step).

## Example: an encounter's lifecycle, conversation to commit

A concrete walkthrough of how a unit of work moves from a developer's request
through to a finished, committed change, tying the World/Campaign/Encounter
pieces above together in practice.

1. **Conversation starts the work.** The developer (GM) describes what they
   want in conversation. Before deciding how the request fits the existing
   model, the agent primes context first - `prime_get` (world summary,
   world-assigned lore, region map, and the active campaign's body, in one
   call).
2. **A campaign is chosen or opened.** If no campaign is already open, the
   agent checks `campaign_list`/`campaign_get` for a fitting `draft`/`paused`
   campaign, or asks the developer whether to create a new one
   (`campaign_create`), then moves it to `open` (`campaign_open`) - only one
   campaign may be open at a time.
3. **The encounter is drafted.** The agent writes the plan as an encounter
   (`encounter_create`), starting in `draft`: `Requirements` (what must be
   true when done), `Rationale` (why), `Plan` (the concrete steps), and
   `Verification` (how completion will be checked). While still `draft`, the
   agent assigns the region(s) the work touches (`encounter_assign_region`)
   and any direct prerequisite encounters (`encounter_assign_dependency`).
4. **The developer approves an independent review.** Drafting alone is not
   approval to review - the agent stops and asks explicitly. Only on an
   explicit yes does it spawn a *fresh* reviewer (never itself, never a
   context-sharing fork) to check the Plan against the encounter's applicable
   lore (`prime_applicable_lore`, then `lore_get` per entry).
5. **The review resolves the draft.** A `PASS-WITH-NOTES` verdict
   auto-transitions the encounter to `reviewed` (`encounter_review`, message
   required) - this permanently locks the four fixed sections against
   replacement. A `REJECT` or `NOT-REVIEWABLE` verdict sends the agent back to
   revise the draft (`encounter_update`, still allowed pre-`reviewed`) and get
   approval again before spawning a fresh reviewer.
6. **The developer approves opening.** With explicit approval, the agent
   moves the encounter to `open` (`encounter_open`) - this fails and lists
   any unmet prerequisite until every `depends_on` entry is `completed`.
7. **The Plan is executed.** The agent does the actual work - writing code,
   docs, tests - against the now-locked Plan. If reality diverges from what
   was planned, or the developer changes the ask mid-flight, the agent
   doesn't rewrite the Plan; it records the deviation and why
   (`encounter_record_message`), valid while `reviewed` or `open`.
8. **Verification runs, then completion is confirmed.** The agent carries out
   the encounter's own Verification steps (tests, lint, manual checks -
   whatever that encounter specified). Once they pass, the agent confirms
   with the developer before closing anything out - never unilaterally - then
   moves the encounter to `completed` (`encounter_complete`).
9. **A commit captures both halves of the change.** The working tree now
   holds two kinds of changes together: the actual deliverable (code, docs,
   tests) and the updated `.sourcebook` state (the now-`completed`
   encounter's frontmatter and its `Log` of review/message/completion
   entries - each one attributed via the local git identity, the same
   identity the eventual commit is made under). A single commit - made by the
   developer, or by the agent once explicitly asked - persists both, so the
   next session's `prime_get` sees not just the code as it now stands, but
   the record of the decision that produced it. This is the continuity the
   framework exists for: session state that survives a context reset because
   it was committed, not held only in a conversation.

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
