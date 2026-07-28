# Crypts and Commits Workflow Reference Guide

## Purpose

### Crypts and Commits

Crypts and Commits ("CAC") is a Coding Assistant Continuity Framework: a way
of structuring collaboration between a developer and an AI coding assistant
using a tabletop-gaming metaphor. The developer plays Game Master,
establishing context, making judgment calls, and retaining final authority
over the session; the assistant plays through that context to get work done.
The `cac` CLI and its MCP server are how an assistant records project context
and tracks its own work across sessions, so continuity survives context
resets and session boundaries instead of being rebuilt from scratch each
time. `.sourcebook/` is where that context and work history live.

### This document

This guide is the single source of truth for the structure of the `.sourcebook`
domain model: the five content types it holds, the attributes and body shape
of each, the workflow/status lifecycle each one follows (where it has one),
and how the types connect to one another. It exists so that implementation-
specific agent skills (Claude Code, Codex, and any future assistant flavor)
can be authored *against* this shared spec instead of one flavor being
treated as the de facto "primary" and the others hand-forked from it.

This is a reference to the domain model's current, real behavior - not a
design proposal and not a historical record of how it used to work. When the
model changes, this document should change with it.

Two interaction surfaces exist over this model: the `crypts-and-commits` MCP
server (the primary surface for an agent session) and the `cac` CLI (a
fallback for when the MCP server isn't available, and the surface a human
developer uses directly). Both expose the same operations; this guide notes
the MCP tool name and CLI command for each, but describes the model itself,
not step-by-step usage instructions - those live in the `world-manager` and
`campaign-manager` agent skills.

## Domain model at a glance

Five content types, each stored as a markdown file with YAML frontmatter
under `.sourcebook/`:

| Type      | Cardinality           | Has a status lifecycle? |
|-----------|------------------------|--------------------------|
| World     | Singleton              | No                       |
| Lore      | Many                   | No (simple enabled/disabled flag, not a guarded lifecycle) |
| Region    | Many                   | No                       |
| Campaign  | Many (one active/`open` at a time) | Yes: `draft` -> `open` -> `paused`/`completed`/`abandoned` |
| Encounter | Many, nested under a campaign | Yes: `draft` -> `reviewed` -> `open` -> `completed`/`abandoned` |

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

- **Frontmatter**: `name`, `assigned_lore` (list), plus the common
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

- **Frontmatter**: `name`, `status`, plus the common stamps.
- **Body**: free-form description of the initiative. Once a campaign reaches
  a terminal status, a dated, attributed **postmortem log entry** is appended
  to the body and the body is locked (`campaign_update`/`cac campaign update`
  will fail).
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
  | `completed` | - | - | Terminal; no further transitions. |
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
      completed --> [*]
      abandoned --> [*]
  ```

- **Connections**: contains its encounters (by directory nesting); an
  encounter records its parent campaign's name on its own frontmatter.

| Operation | MCP tool | CLI fallback |
|---|---|---|
| Read | `campaign_get` | `cac campaign get` |
| List (name + status) | `campaign_list` | `cac campaign list` |
| Create (starts `draft`) | `campaign_create` | `cac campaign create` |
| Replace body | `campaign_update` | `cac campaign update` |
| Delete | `campaign_delete` | `cac campaign delete` |
| Open | `campaign_open` | `cac campaign open` |
| Pause | `campaign_pause` | `cac campaign pause` |
| Complete (+ postmortem message) | `campaign_complete` | `cac campaign complete` |
| Abandon (+ postmortem message) | `campaign_abandon` | `cac campaign abandon` |

## Encounter

A concrete unit of work within a campaign: a plan the agent is expected to
execute, with fixed body sections.

- **Frontmatter**: `name`, `campaign` (parent campaign name), `status`,
  `regions` (list), `depends_on` (list of direct prerequisite encounter names
  within the same campaign), plus the common stamps.
- **Body**: four fixed sections - `Requirements`, `Rationale`, `Plan`,
  `Verification` - plus an appended `Log` section once any transition or
  message carries a message. The four fixed sections may only be *replaced*
  while status is `draft`; every later change is an append (via a
  transition's message, or `encounter_record_message`), never a rewrite.
- **Status lifecycle**:

  | From | To | Trigger | Notes |
  |---|---|---|---|
  | `draft` | `reviewed` | `encounter_review` | Message required. Requires at least one assigned region. Performed by an independent reviewer (see the `campaign-manager` skill), never the plan's author. Permanently locks the four fixed sections. |
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

| Operation | MCP tool | CLI fallback |
|---|---|---|
| Read | `encounter_get` | `cac encounter get` |
| List (oldest-updated first) | `encounter_list` | `cac encounter list` |
| Show in dependency order | `encounter_order` | `cac encounter order` |
| Create (starts `draft`) | `encounter_create` | `cac encounter create` |
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

What is *not* separately gated: the draft -> reviewed transition itself, once
a `PASS-WITH-NOTES` verdict is in hand - it runs immediately, because gate 1
already covers it. Campaign-level transitions (`open`/`pause`/`complete`/
`abandon`) and lore/region/world edits have no codified approval gate of
their own in this model; they take effect as soon as the corresponding
mutating tool is called.

## Cross-cutting: priming and search

Two auxiliary capabilities sit on top of the five content types above -
neither is a content type itself:

- **Prime** (`prime_get` / `cac prime get`, `prime_applicable_lore` /
  `cac prime applicable-lore`) assembles cross-object context in one call
  instead of chaining individual reads: the world, world-assigned enabled
  lore summaries, the region map, and the active campaign's body in one
  round trip; and, for a specific encounter, the exact enabled lore set that
  applies to it (world-assigned union its assigned regions' lore).
- **Search index** (`index_status` / `cac index status`, `index_search` /
  `cac index search`) is a full-text index over `.sourcebook` content kept in
  sync automatically as content changes through `cac`. Rebuilding it
  (`cac index rebuild`) is developer-only and intentionally not exposed over
  MCP.

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
