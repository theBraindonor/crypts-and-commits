# Crypts and Commits Development Workflow

## Purpose and authority

Crypts and Commits ("CAC") preserves a coding assistant's context and work
history across sessions. The developer is the Game Master and keeps final
authority. Assistants use the MCP server first, or the cac CLI when unavailable;
managed sourcebook content is never read or edited directly.

This guide owns campaign selection, registration, execution, encounter lifecycles and review.
Shared rules are repeated in both phase guides so ordinary work needs one deep
workflow retrieval. Planning is the primary home for static context, bosses,
record triage, priming, synchronization and numbering. Development is the primary
home for campaign lifecycle/coupling, reconciliation, encounter gates and capture.
Update a primary rule and every affected mirror in the same change; divergent
copies are documentation defects to reconcile against the primary and implementation.
Primary ownership guides maintenance, not a mandatory second retrieval.

The [Planning Workflow](planning-workflow.md) covers
goal editing, roadmap adoption, triage and maintenance detail.
The [Tool Reference](tool-reference.md) owns MCP/CLI names, arguments, results,
errors, budgets and continuation; these guides own procedural meaning. Keep the
owning guide and affected mirrors accurate in the same substantive change.
[workflow](workflow.md) is only a routing index.

Read this guide through `docs_get("development-workflow")` /
`cac docs get development-workflow` only when a procedural question remains;
routine orientation uses prime and the skills. Bootstrap and index rebuild are
developer-only. Branch settings name branches; they neither create them nor prove
integration. A skill grants no blanket publication or merge authorization.

## Domain model at a glance

Eight record types, each Markdown with YAML frontmatter, live in the sourcebook:

| Type | Scope | Lifecycle |
| --- | --- | --- |
| World | Singleton | None |
| Lore | Many | Enabled or disabled |
| Region | Many | None |
| Boss | Project goals | proposed, available, withdrawn, vanquished |
| Campaign | Initiatives; at most one open per checkout | draft, open, paused, completed, abandoned |
| Encounter | Units of work within a campaign | draft, reviewed, open, completed, abandoned |
| Rumor | Backlog notes from anywhere | open, promoted, dismissed |
| Ruling | Developer decisions made during an open campaign | recorded, canonized, noted |

Every record carries common audit stamps (`created_by`, `created_on`,
`updated_by`, `updated_on`).

### Connections

- World and lore links are reciprocal: `world.assigned_lore` and
  `lore.assigned_to_world`.
- Region and lore links are reciprocal: `region.assigned_lore` and
  `lore.assigned_regions`. One lore entry can serve several regions.
- An encounter's applicable lore is the union of enabled world-assigned lore and
  the enabled lore of every region the encounter is assigned to. It is resolved
  on demand and never stored on the encounter. Lore summaries route; full lore
  bodies govern review.
- A campaign contains its encounters. An encounter's `regions` list is
  one-directional: regions keep no back-reference to encounters.
- An encounter's `depends_on` lists direct prerequisites within the same
  campaign, stored only on the dependent. Reverse dependents are computed when
  needed, for example to block deletion.
- Bosses and campaigns link reciprocally: a campaign lists its `bosses`, and
  each linked boss names its current `campaign`. A boss's `depends_on` lists
  prerequisite bosses.
- A promoted rumor's `boss` names the boss it was linked to, stored only on
  the rumor. Bosses keep no back-reference, and many rumors may share one.
- A ruling's `campaign` and `encounter` are stored only on the ruling;
  campaigns and encounters are never written and keep no back-reference.

No relationship grants permission to bypass a lifecycle guard.

## Lore

Lore is a standard, convention or best practice that an encounter is checked
against before it moves from `draft` to `reviewed`. World-assigned lore applies
to every encounter; region-assigned lore applies only to encounters assigned to
that region.

- **Frontmatter:** `name`, `enabled`, `assigned_to_world`, `assigned_regions`,
  `summary`, and the audit stamps. The summary is a routing signal of at most
  500 characters, required with every body write.
- **Body:** the governing rule text. It is what a plan is checked against; the
  summary never substitutes for it.
- **Status:** an `enabled` flag that can be toggled at any time. Disabled lore
  is skipped when resolving applicable lore.

## Region

A region is a documented path in the repository that needs its own
conventions, stack or tooling described (for example "frontend" and "backend"),
and that lore can be scoped to.

- **Frontmatter:** `name`, `path`, `assigned_lore`, `summary` (same rule as
  lore), and the audit stamps. The path is not validated against the
  filesystem, so a region may describe planned work.
- **Body:** free-form documentation of the region.
- **Status:** none. Encounter assignments are recorded only on the encounter.

## Candidate discovery

Candidate discovery explains which goals could be selected for a campaign. It
is read-only and is not proof of integration. Numbered names sort by number,
then by name, and legacy names follow lexically; this order is not business
priority or permission to select.

The pool is every live, unassigned boss in proposed or available status.

- A proposed boss is `not_ready`.
- An available boss is `eligible` only when every direct prerequisite is
  vanquished (an archived completion counts) and the reachable graph is
  intact; otherwise it is `blocked`.
- Every other boss is excluded from the pool. Discovery never changes
  readiness.

Campaign links must resolve, reciprocate and match lifecycle and archive state:
an available boss belongs with a draft, open or paused campaign, and a
vanquished boss with a completed one. Archived defects still affect health.
Unrelated damage does not hide healthy choices, and the counts distinguish an
empty pool from excluded, unready and blocked goals. Defects reachable from a
dependent block it.

## Campaign

A campaign is a long-running initiative, similar to an epic, expected to span
many encounters.

- **Frontmatter:** `name`, `status`, the canonical `bosses` list (empty for a
  bossless campaign), `archived` (default false), and the audit stamps.
- **Body:** a free-form description of the tactics. When the campaign is
  completed or abandoned, a dated and attributed postmortem entry is appended
  and the body locks. Explicit reactivation can reopen a completed campaign.

| From | To | Trigger | Guard and effect |
| --- | --- | --- | --- |
| draft | open | open | Only one campaign may be open; the call names the other open campaign. |
| draft | abandoned | abandon | Postmortem message required. |
| open | paused | pause | Fails while any encounter is open. |
| open | completed | complete | Fails while any encounter is open. Postmortem required; locks the body. |
| open | abandoned | abandon | Same open-encounter guard, postmortem and lock. |
| paused | open | open | Same single-open guard. |
| paused | completed | complete | Same as open to completed. |
| paused | abandoned | abandon | Same as open to abandoned. |
| completed | open | reactivate | Unarchived only; nonblank reason and single-open guard. Keeps closing history. |
| abandoned | none | none | Terminal. |

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

A campaign can be deleted only when its `bosses` list (current or historical
membership) is empty and no boss claims it. Deletion is never a rollback or
renumbering shortcut.

### Archiving

`archived` is a flag, not a status. Archiving never changes the campaign's
status. It moves finished work out of the live campaign and encounter
directories into the sourcebook's archive area, keeping the same layout one
level down.

A campaign can be archived only when its status is completed or abandoned, it
is not already archived, and every one of its encounters is completed or
abandoned. That is broader than the open-encounter guard on complete, pause and
abandon, which lets draft and reviewed encounters through. Archiving a
campaign archives all of its encounters in the same atomic operation; there is
no standalone encounter archive and no unarchive operation.

Archived records stay readable by name and stay in the search index, updated in
place. Lists and search exclude archived records unless asked to include them.
Reading an archived record never restores it. The effects of archiving on
linked bosses are described under "Promotion and campaign coupling".

## Promotion and campaign coupling

A campaign has zero or more bosses, and a boss has at most one current
campaign. There is no primary boss.

Selection creates a new draft campaign and links it to every selected boss in
one atomic step. Each boss must be eligible, unassigned, unarchived and
available. Selecting a prerequisite together with its incomplete dependent does
not satisfy the dependency. Selection leaves the bosses available but frozen,
and opens no campaign and creates no encounters. A new campaign name must be
unused, live or archived, and unclaimed. The single-goal convenience
(`boss_assign_campaign`) behaves the same way for one boss; a consistent retry
is read-only, even after progress, archiving or group membership, and never
shrinks membership. A retry against a different or released campaign fails.
Initial selection checks full eligibility; retries do not recheck
prerequisites.

While a campaign is in draft, its whole membership can be replaced with a
nonblank reason. Retained members must still reciprocate, and removal releases
only this campaign's links. Membership locks once the campaign leaves draft,
including after reactivation, and body edits can never change links.

Lifecycle effects on bosses:

- **Completion** records the postmortem and vanquishes every linked boss.
- **Abandonment** releases every current link while keeping the historical
  membership list on the campaign.
- **Reactivation** requires an unarchived completed campaign, a nonblank
  reason and no other open campaign. Every linked boss returns to available
  but stays assigned and frozen. The earlier Log and closed encounters remain,
  and recompletion appends new history.
- **Open and pause** never vanquish. Bossless campaigns follow the same
  lifecycle.

Archiving a completed campaign moves its assigned bosses along with its
terminal encounters, preserving status and readable history. Archiving an
abandoned campaign never touches released bosses, whatever has happened to
them since. Rumors are never touched. Current and historical membership lists
and reverse claims protect against deletion. Broken or competing ownership, or
an inconsistent lifecycle state, blocks mutation until it is repaired.

## Encounter

An encounter is a concrete unit of work within a campaign.

- **Frontmatter:** `name`, `campaign`, `status`, `kind`, `regions`,
  `depends_on`, `archived` (only ever set by archiving the campaign), and the
  audit stamps.
- **Body:** a scripted encounter has four fixed sections: Requirements,
  Rationale, Plan and Verification. An unscripted encounter has only
  Requirements and Rationale. Either kind gains a Log section once a
  transition or message records text. The fixed sections can be replaced only
  while the encounter is in draft; every later change is appended to the Log.

| From | To | Trigger | Guard and effect |
| --- | --- | --- | --- |
| draft | reviewed | review | Message required; at least one region assigned. Performed by an independent reviewer, never the author; a REJECT passes only by explicit developer override (see Review flow). Locks the fixed sections. |
| draft | abandoned | abandon | Message required. |
| reviewed | open | open | Optional message. Fails until every direct prerequisite is completed. |
| reviewed | abandoned | abandon | Message required. |
| open | completed | complete | Optional message. |
| open | abandoned | abandon | Message required. |
| completed, abandoned | none | none | Terminal. |

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

Recording a message without a status change is allowed only while the
encounter is reviewed or open. Region and dependency assignments are allowed
only while it is in draft. A dependency must name a non-abandoned encounter in
the same campaign and cannot create a self-dependency or a cycle. A prerequisite
that is abandoned after assignment remains an unsatisfied blocker until it is
removed or replaced. An encounter cannot be deleted while another encounter
depends on it.

Encounters in a completed or abandoned campaign cannot be changed, but they
remain readable so past work stays inspectable.

### Kind: scripted and unscripted

`kind` is set once, at creation, and never changes.

- **Scripted** (the default) is a plan for future work. The reviewer checks the
  Plan against applicable lore.
- **Unscripted** records work that the developer or agent already did outside
  the plan-first flow, so a later session can recover its intent. Only
  Requirements (what was done) and Rationale (why) apply, and the absence of a
  Plan or Verification is not a defect. The lifecycle, the independent review
  and all three user gates are the same as for scripted work; the reviewer
  checks the recorded Requirements and Rationale in place of a Plan.

## Explicit user gates

Three points in the encounter lifecycle need the developer's explicit,
real-time approval. Reaching the status before a gate is never consent to cross
it: the agent stops, asks, and waits for an explicit answer every time.

1. **Before spawning the independent reviewer** (the prerequisite for draft to
   reviewed). Drafting is not approval to review. Ask fresh every time,
   including for a re-review after a REJECT or NOT-REVIEWABLE verdict and a
   revised draft. Only on an explicit yes does the agent spawn a fresh reviewer
   subagent: never itself, and never a fork that shares the author's context.
2. **Before opening the encounter** (reviewed to open). This is separate from
   gate 1. A PASS-WITH-NOTES verdict, or the developer's explicit override of
   a REJECT, moves the encounter to reviewed without a further pause, because
   gate 1 or the override already covered it, but starting execution is its own
   request, including after an override.
3. **Before marking the encounter complete** (open to completed). After
   Verification passes, the agent confirms with the developer before closing
   it, even when every check is green.

Both `campaign_manager` skill templates
(`templates/skills/claude/campaign_manager/SKILL.md` and
`templates/skills/codex/campaign_manager/SKILL.md`) must state each gate's
stop-and-ask instruction in their own wording, so that an agent following the
skill alone, with no memory of this guide, would still stop and ask. A
cross-reference to this guide is not enough. This holds every time either
template is edited or regenerated, for any reason. An edit that drops, weakens
or fails to carry forward any gate is a defect, caught by checking the
template's current text against this section.

### Review flow

The reviewer receives only the encounter and campaign names. It primes context
itself, resolves applicable lore, reads each lore body, and checks the Plan (or
an unscripted encounter's Requirements and Rationale) within a bounded reading
surface: the encounter, the applicable lore bodies, the assigned regions'
paths, and files the encounter names. It flags anything outside that surface as
unverified rather than investigating it. It returns findings, one verdict
(PASS-WITH-NOTES, REJECT or NOT-REVIEWABLE) and a proposed review message, and
it runs no mutating operation.

On PASS-WITH-NOTES, the main thread immediately records the reviewer's proposed
message through `encounter_review`, which locks the fixed sections, and then
reports. Later feedback is recorded as a message, never as a re-draft. On
REJECT or NOT-REVIEWABLE, the encounter stays in draft; the agent revises it
and returns to gate 1. An absent Plan or Verification is never by itself
grounds for NOT-REVIEWABLE on an unscripted encounter.

On REJECT only, the agent may offer the developer an explicit GM override; it is
never assumed or self-granted. If the developer overrides with a stated reason,
that is the draft-to-reviewed authorization: the agent records `encounter_review`
with the reviewer's findings verbatim followed by the override and its reason,
and captures the reason as a ruling. NOT-REVIEWABLE has no override.

## Codex encounter handoffs

The Codex `campaign-manager` skill adds two conversational reports. They
supplement the encounter record and preserve all three gates. The skill carries
the full operative guidance; this section states what the reports must cover.

Each report stands on its own: the developer should be able to understand the
work or the review outcome and make the next decision without opening the
encounter. Include the encounter's full reference. Scale depth to complexity
and uncertainty, explain why details matter, and avoid a fixed word count,
padding, or pasting the encounter.

**After drafting, before asking to review,** explain the encounter's identity,
kind and draft status; the problem, motivation and intended outcome; scope,
affected areas, main steps and significant tradeoffs; dependencies,
assumptions, risks and unresolved decisions (saying so when there are none);
and the verification approach and success criteria. For unscripted work,
describe what was done, why, the evidence and any follow-up instead of a
future plan. After revising a rejected draft, explain what changed, why it
addresses the findings, and what remains open.

**After every review,** explain the verdict and its coverage and limits, each
material finding with its reasoning and importance (separating blockers,
actionable notes and unverified concerns), the consequences for scope, risk and
readiness, the resulting status and locking, and a reasoned recommendation with
the next approval needed. On PASS-WITH-NOTES, transition first, then report and
ask separately to open. On REJECT or NOT-REVIEWABLE, keep the draft, explain
the blockers, and after revising ask again before launching a fresh reviewer;
revision alone is not a passing review. After a developer override of a
REJECT, transition first with the override message, then report and ask
separately to open. Never replace or rewrite the
reviewer's recorded message, and keep your own recommendations distinct from
its findings. A recommendation never authorizes a review, an opening or a
completion.

## Rumors

A rumor (`rNNN-slug`) is a backlog note, "we think X should be done", from
anywhere: execution, a review, a customer, the running project. It carries a
summary, a free-text `origin` and an optional body, and can be captured on any
branch. Only `open` rumors can be edited.

- **Promote** (`open` to `promoted`) links the rumor to an existing unassigned
  `proposed` or `available` boss, recorded only on the rumor; the boss is never
  written. Many rumors may share a boss.
- **Dismiss** (`open` to `dismissed`) requires a reason; **reopen** returns
  either to `open` with a message. **Archive** retires a promoted or dismissed
  rumor read-only. There is no delete, and transition messages stay in
  `history`.

Numbers captured on different branches can collide. They are renumbered on the
planning branch; promoted rumors keep their number, because promotion happens
on planning, where numbering is settled. Similar rumors are never merged:
repetition is a signal. Rumors never affect bosses, candidates or campaign
lifecycle, are searchable under their own type, and are not part of prime.

## Rulings

A ruling (`cNNN-eNNN-slug`, canonical names only) records a developer decision
made during active development, such as an answered open question or an
overridden reviewer REJECT. Create requires the `cNNN` campaign to be `open`
(reactivated qualifies) and a nonzero `eNNN` to be one of its encounters; `e000`
marks a campaign-level decision. With no open campaign,
capture a rumor instead. Slugs are unique, live or archived.

A new ruling is `recorded` and stays editable until planning disposes of it in
hindsight: **canonize** with a narrative of the world, lore or region updates
made, or **note** with a narrative of why none is needed. Either narrative
becomes `resolution`; **reopen** returns it to `recorded`. Rulings name no lore,
region or world records. **Archive** retires a canonized or noted ruling, independently of
campaign archival. There is no delete. Rulings are searchable under their own
type, and recorded rulings appear in prime until triaged.

## Actions not separately gated

Not separately gated: the draft-to-reviewed transition itself once a
PASS-WITH-NOTES verdict or a developer override of a REJECT is in hand, ruling
capture, campaign transitions, and lore, region and
world edits. Those take effect when the tool is called, subject to the
authorization rules in "Agent planning and campaign workflow".

## Priming and the disclosure ladder

world-manager carries the disclosure ladder, the procedure for loading only as
much context as a task needs:

1. **Orient** with `prime_get`, once per session or before other work. It
   returns the full world, world-lore summaries, the region map, the active
   campaign body, the active bosses with diagnostics, and recorded (untriaged)
   rulings as summaries. Hydrate truncated
   bodies through the refs it returns. Empty membership is different from a
   named member that is missing or broken.
2. **Focus** on a region when one is in scope: read the region, then the
   summaries of its assigned lore.
3. **Review** with `prime_applicable_lore` for an encounter, following
   `next_cursor` until it is null, then read each applicable lore body in
   full. Only the bodies are authoritative.
4. **Go deeper** only when a procedural or contract question remains. Read
   the Planning Workflow for goals, triage, context or maintenance, the
   [Development Workflow](development-workflow.md) for campaigns, encounters
   and approval gates, the Tool
   Reference for an argument, result shape, error or budget, the branching
   guide for a worked Git example, and the migration guide for upgrades and
   adoption. `docs_list` shows what is registered.

campaign-manager and world-planner start from step 1 and do not read this
guide or the Tool Reference during routine orientation. Their skills name the
section to consult when a question arises. Most sessions never need step 4.

The search index is a full-text index over sourcebook records, kept current as
records change through CAC. It finds encounter text, but it is not an
allocation inventory or a dependency graph. A stale or missing index needs a
developer rebuild.

## Agent planning and campaign workflow

### Ownership

- **world-manager** owns static context: the world, lore, regions, the
  disclosure ladder and migration routing.
- **world-planner** owns goals: planning, roadmap adoption, readiness,
  dependencies and splitting, triaging integrated rumors (renumbering,
  promotion and dismissal) and recorded rulings (canonizing or noting), and
  planning-side archival.
- **campaign-manager** owns tactical work: selection and registration, draft
  membership, encounters and execution. Any skill captures rumors, and any
  skill working in an open campaign captures rulings.

Both provider variants of each skill implement this procedure. Invoking a
skill is not blanket permission to publish, push, merge, delete, or message
other people. Use authorization the developer has already given without asking
again. The [encounter gates](development-workflow.md#explicit-user-gates) stay distinct; ordinary goal notes have no
encounter gates.

### Orient and synchronize

Read prime and the effective branch settings. Prime's bosses are the active
campaign's membership, not the whole roadmap. Finish every page of an
inventory, and hydrate the bodies and diagnostics you rely on. Bootstrap and
index rebuild are developer-only.

Before editing goals or selecting them, synchronize accepted merge-target
history onto the planning branch under the project's Git policy. Check the
checkout, branch, uncommitted changes and detached HEAD state, and reconcile any
mismatch without silently switching branches or overwriting work. Refresh
authorized remote refs on a best-effort basis and say when you could not.
Local completion is not integration, and a roadmap's completed status is
supplied evidence, not proof of a CAC merge.

### Allocate numbers

CAC numbers bosses, campaigns, encounters and rumors by convention: core never
allocates. Choose the numeric maximum plus one, padded to three digits below
1000 and continuing at 1000. Never reuse a retained ID, and never infer the
maximum from lexical, time or search order.

- **Bosses:** every page of the boss list including archives, on a
  synchronized planning branch.
- **Campaigns:** every page of the campaign list including archives, plus known
  local and remote campaign branches, including unpublished reservations. A
  matching `c00N-example` and `c00N-example-assignment` pair counts once.
- **Encounters:** every page of the encounter list including archives, within
  the exact campaign.
- **Rumors:** every page of the rumor list including archives, on the current
  branch. Rumors may be numbered on any branch; collisions found after
  integration are renumbered on planning.
- **Rulings:** not numbered. Name each `cNNN-eNNN-slug` for the open campaign
  and current encounter (`e000` when none), with a slug unused among live and
  archived rulings.

Unnumbered legacy names remain valid. Ambiguous shorthand requires the
canonical name.

### Select and register

Write tactics that cover every developer-selected eligible goal and its success
conditions. On the assignment branch (`c00N-example-assignment`, created from
the synchronized merge target), create the draft campaign with its bosses, or
use the single-goal convenience. Confirm the reciprocal links, and inspect any
error and its rollback. Integrate the registration through the project's PR or
direct-merge process before execution. Selection opens nothing and creates no
encounters. A bossless campaign may skip registration and start directly on
its execution branch, with the same allocation checks.

### Execute on the campaign branch

Create or resume the execution branch (`c00N-example`) from the accepted
registration or the merge target; if starting from the assignment branch,
reconcile the accepted registration first. Open the campaign only on its
execution branch and only with explicit approval. Under the recommended
workflow, the merge target and planning branches never have an open campaign,
and paused work stays on its execution branch. These are skill guidance, not
endpoint gates or mandatory CI or hosting rules. Honor custom branch settings.
Draft membership changes need a reason; opening or reopening locks membership.
Boss designs stay frozen.

### Capture rulings

When the developer confirms an answer to an open question or choice in an open
campaign (a boss or encounter open question, a plan choice, or the reason for
overriding a REJECT), record it as a ruling in the same exchange. Record only
what the developer confirmed (decision, context, consequences), with the
developer as origin. Never ask whether it matters enough; planning judges that
in hindsight. A ruling never replaces the encounter's own record: deviations
still go to its log, and follow-up ideas for frozen bosses still become
rumors. Capture needs no separate approval, but never change a ruling's
meaning without the developer. With no open campaign, capture a rumor.

### Collision checks

Check for logical collisions when creating a campaign or encounter, after
integrating another branch (pull, merge or rebase), and before completion when
preparing implementation for integration; repeat after review fixes. Compare
numeric IDs and names, encounter IDs within the campaign, and reciprocal
ownership of every boss. A clean Git merge does not detect two records with the
same number and different slugs, or competing assignments. Explain any conflict
and coordinate an explicit repair. Never silently renumber, delete, force-push,
reset, or edit managed files directly.

### Complete and reactivate

Complete a campaign only after its goals and encounters are verified, with the
required postmortem and the developer's authorization. Completion vanquishes
every linked goal; abandonment releases every current link while keeping the
historical membership. For review fixes before merging, reactivate with a
reason on the execution branch, keep membership and history, add reviewed
follow-up encounters (completed encounters never reopen), verify, and complete
again. New scope after merging goes back to planning. Integrate terminal
execution records before planning relies on their outcomes. Publishing and
merging need the developer's authorization.

### Reconciliation examples

- **Rejected registration.** Establish whether the registration was integrated
  and inspect the visible assignment and execution branches. Revise it or
  abandon it explicitly, keeping useful notes and the number reservation. Never
  present a rejection as acceptance, and never delete automatically.
- **Accepted draft cancelled before execution.** Abandon the campaign with a
  reason on its execution branch, integrate that cleanup, and synchronize the
  planning branch. Do not release links by hand.
- **Legacy unnumbered open work.** Inspect its encounters and local
  instructions, and agree on a matching execution branch and naming with the
  developer. Finish or abandon open encounters before pausing or closing.
  Preserve history: do not invent a boss, bulk-rename records, or add a new
  endpoint branch gate.
- **Uncertain remote or integration state, or a failed recovery.** Stop and
  reconcile explicitly with the developer.


For integrated rumor/ruling triage and archival, follow the
[Planning handoff](planning-workflow.md#planning-handoff). Capture does not
expand the campaign's scope or edit frozen goal designs.

## Example: an encounter's lifecycle

1. Orient with prime. If no campaign fits the task, world-planner helps capture
   or choose goals; capturing a goal does not assign it.
2. With authorization, campaign-manager selects eligible goals, writes a
   tactical draft, and registers it on `c00N-example-assignment`. After the
   registration is accepted, it switches to `c00N-example` and opens the
   campaign with explicit approval. A bossless campaign skips registration.
3. Draft the encounter (for example `c00N/e00M`) with its sections, regions
   and prerequisites. Unscripted work records only Requirements and Rationale.
4. Ask for approval to review, then spawn a fresh reviewer with only the two
   names. It reads the applicable lore bodies itself.
5. On PASS-WITH-NOTES, record the reviewer's message, which locks the
   sections, and report. On REJECT or NOT-REVIEWABLE, revise and ask again,
   or, on REJECT, the developer may override with a reason, which is recorded
   and captured as a ruling.
6. Ask separately for approval to open. Opening requires every prerequisite to
   be completed.
7. Execute the Plan, logging deviations as messages rather than editing locked
   sections.
8. Run Verification (or confirm an unscripted record's accuracy), then ask the
   developer to confirm completion before completing.
9. When asked, commit the deliverable together with the encounter record.
   Completing an encounter does not authorize completing the campaign, pushing
   or merging.
