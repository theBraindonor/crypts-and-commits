# Boss Edition: goals before campaigns

Status: design draft for the next release. This document proposes behavior; it
does not describe shipped commands or approve implementation encounters.

## Problem

Campaign planning is a point of friction in Crypts and Commits (CAC). Ideas need
somewhere to evolve before the developer commits to an initiative. Creating a
campaign too early mixes exploratory design with chosen work, while keeping
notes outside CAC makes future intent difficult for an agent to recover.

The feature should help an agent answer:

> If there is no active campaign, which project goal should we take on next,
> and why?

A **boss** represents a project goal or challenge. Its notes explain the problem,
desired outcome, design considerations, and prerequisites. A campaign represents
the effort chosen to defeat that boss; encounters remain the concrete units of
work within the campaign. Defeating one boss completes an initiative, not
necessarily the entire project.

## Decisions established so far

- Bosses provide a knowledgebase for future goals without requiring campaigns.
- Notes can evolve freely before a boss is selected.
- Dependencies and precedence must be visible when choosing future work.
- One boss has at most one current campaign assignment. A goal requiring multiple
  successful campaigns must be split before selection. Abandoned attempts release
  their assignment so another campaign can pursue the same boss.
- Selection creates a campaign reference and makes the boss read-only.
- Boss assignment occurs when the draft campaign is created, before encounters.
- Campaign branches may capture freeform rumors for later planning without
  modifying boss records. Planning engineers decide how to distill them.
- Bosses, campaigns, and encounters use numbered names: `bNNN-boss-slug`,
  `cNNN-campaign-slug`, and `eNNN-encounter-slug`, expanding beyond three digits
  when needed. Skills allocate numbers; CAC's core does not.
- Campaigns are the workflow spine. Each campaign is edited and activated on a
  branch named exactly after it; no campaign is active on `main`.
- Branch rules are skill guidance. The CLI and MCP endpoints are branch-agnostic:
  their behavior never changes with the current branch, so projects can adopt
  custom branching strategies. Skills know the intended branch for each operation
  and guide the developer accordingly.
- Git is foundational to this workflow. Projects without a Git repository are
  out of scope.
- Pull requests are not required. A solo developer may merge a local branch into
  `main` directly, following the same flow a PR would.
- Archiving is a flag, not a status, matching existing campaigns and encounters.
  Archiving campaigns and their bosses happens on the planning branch.
- `vanquished` is the boss's successful-completion status, set when its campaign
  completes.
- Encounter numbering starts at `e001` within each campaign. References such as
  `c001/e011` identify an encounter without repeating its descriptive slug.
- Multi-agent messaging, assignment, supervision, and distributed coordination
  belong outside CAC. Bosses must remain useful without those systems.

Bosses are aspirational; campaigns are tactical plans crafted to meet their
boss's requirements. Boss dependencies are optional hard prerequisites referencing
other bosses. Planning has a dedicated skill, and merge-policy enforcement is
skill-based; CI validation is entirely the developer's choice.

The remaining implementation details below are proposals unless explicitly agreed.

## Scope and boundaries

The first release should support capturing and refining bosses, maintaining
prerequisites, explaining available choices, and promoting a boss into a draft
campaign while preserving its original intent.

It should not introduce an agent runtime, shared inbox, chat service, scheduler,
distributed claim service, or a dependency on MCP Agent Mail. Such a service can
coordinate agents using CAC records as references. It does not become the source
of truth for the goal's definition or campaign history.

The one-active-campaign rule becomes branch-scoped. Different developers can
work on different campaign branches at the same time, each with its own active
campaign. This does not establish globally consistent state across independent
clones or provide distributed assignment and supervision.

## Naming, numbering, and branch workflow

### Configurable branches and guidance

Store two branch names in the world record:

| Proposed attribute | Default | Purpose |
| --- | --- | --- |
| `merge_target_branch` | `main` | Integration branch that campaign and assignment work merges into |
| `planning_branch` | `planning` | Branch where bosses are managed and rumors distilled |

Throughout this document, `main` and `planning` are shorthand for these
configured branches: `master`, `trunk`, or another project integration branch
is equally valid, and a project can rename the planning branch to avoid
colliding with an existing branch. Skills use these settings when creating
planning/campaign branches, synchronizing, and targeting merges.

Branch conventions and integration checks are skill guidance only. The CLI and
MCP endpoints do not inspect the current branch, and their behavior never
differs by branch; this keeps them simple and leaves room for custom branching
strategies. Preserve existing core lifecycle validation (for example, at most one
open campaign in a checkout), but do not add branch-dependent validation. Skills
check the branch, explain mismatches, and let the developer and assistant
reconcile them. This release does not require centralized Git state, mandatory
CI, or automatic proof of merge completion.

Pull requests are the default way to integrate, but they are not required. A
solo developer may merge a local assignment or execution branch into `main`
directly; this follows the same flow a PR would, without a hosting service.
Throughout this document, "PR" means either form of integration.

### Canonical names and references

| Object | Canonical name example | Number scope | Short reference |
| --- | --- | --- | --- |
| Boss | `b001-improve-planning` | Project | `b001` |
| Campaign | `c001-boss-edition` | Project | `c001` |
| Encounter | `e011-add-candidate-discovery` | Campaign | `c001/e011` |

Use lowercase hyphenated descriptive slugs. The letter and number provide the
identity; the slug makes records and branches readable. Boss and campaign
numbers are independent: `b007` may become `c012`. Numbering records allocation
order, not priority, dependency order, or release version.

Start at 001, pad numbers below 1000 to three digits, and continue with 1000
without renumbering earlier records. Compare numeric values rather than sorting
the formatted identifiers lexically. Never reuse an allocated number after
completion, withdrawal, abandonment, or archiving. Proposed default: avoid
renaming canonical names in the first release; rename support would need to
preserve the numbered identity and resolve historical references.

Resolve `c001/e011` by campaign number and then encounter number, returning the
canonical names. A bare `e011` is meaningful only within an explicitly selected
campaign or the active (open) campaign. Reject ambiguous short references;
never choose whichever matching slug appears first. Persist references using a
consistent canonical representation and expose both full names and short refs
through the CLI and MCP interfaces.

### Campaign branches

Use an assignment branch and an execution branch, without an extra prefix:

1. Check known campaign records and local/remote branches for collisions.
2. Create `cNNN-slug-name-assignment` from updated `main`.
3. Create a draft campaign with its boss reference and set the reciprocal
   campaign reference on the boss. Freeze the boss's planning content.
4. Issue a small assignment PR into `main` to register the assignment and notify
   the team. Aim for fast automated merging under the repository's normal policy.
   Resolve collisions and merge conflicts manually before proceeding.
5. Create `cNNN-slug-name` from updated `main`, or from the assignment branch.
   When using the latter, reconcile the accepted registration before opening.
6. Finish drafting and open the campaign on its execution branch. Perform the
   campaign's encounters there, checking collisions after branch integrations.
7. Check collisions before completing the campaign for its implementation PR.
   Complete the campaign and issue the PR into `main`.
8. If review requires changes, reactivate the campaign on its execution branch,
   do and verify the follow-up work, and complete it again before merge.

A bossless campaign may skip the assignment branch and registration PR and be
created directly on its execution branch. Campaign discovery skills inspect known
branches as well as records, so unpublished-to-main campaigns remain discoverable
to the extent those branches are visible. Keep the same numbering/collision checks.

The execution branch exactly matches the campaign name. The matching assignment
and execution branches represent one allocation, not a collision. Reserve the
`-assignment` suffix for registration branches.

This is a recommendation for the upcoming feature, not an instruction to create
or switch branches while writing this design document.

Active campaign resolution in core is unchanged: the active campaign is the
checkout's single `open` campaign record. The workflow makes this branch-scoped
in practice. Campaigns are opened only on their execution branches and are
completed or abandoned before merging, so `main` and `planning` never carry an
`open` campaign, and each execution branch carries at most its own.

Under the intended workflow:

- On `main`, no campaign is active and none should be opened.
- On a campaign's execution branch, only that campaign should be active, and
  campaign and encounter mutations for it happen there.
- On its assignment branch, only draft creation and reciprocal boss-link
  registration happen.
- Campaigns are not opened on assignment or planning branches.

Skills enforce these expectations, not the endpoints. Before planning or
resuming execution, skills check the current branch (using Git directly), flag
unrelated branches or detached HEAD, and guide the developer to the appropriate
branch. A mismatch is something to explain and reconcile, never a reason for an
endpoint to refuse an operation.

Other campaign records may be present in a checkout as shared history. Their
presence does not make them active or prevent the branch's campaign from opening.

Assignment PRs intentionally register draft campaigns on `main`, where they are
inactive. Implementation PRs require completed campaigns, including after review
fixes. A paused campaign remains on its execution branch. Abandonment is a
terminal status like completion: abandon the campaign on its execution branch
and merge that branch into `main` the same way as a completed campaign, so the
abandoned record and its released boss assignment become shared history.

Skills perform pre-PR checks. Optional CI validation can reinforce the policy;
branch checks alone cannot prevent an external Git merge. CAC need not host PRs
or bypass repository review and branch protection policies.

### Planning branch and boss records

Create the planning branch (configured name, default `planning`) from `main`.
Boss records live in the managed `bosses` directory of the sourcebook. Create
and edit their notes, summaries, dependencies, and lifecycle through CAC's
MCP/CLI interfaces on `planning`. Assigned bosses' design content remains
read-only. Select the next boss number from the highest existing boss number,
including archived records.

Pull `main` before planning edits. Publish planning work into `main` through a
PR, or a direct merge for a solo developer, before any assignment depends on it.
Planning is meant to be frequent: regular planning sessions keep a supply of
available boss candidates ready for development. Keep `planning` synchronized
with `main` so accepted assignments become visible and stale planning copies do
not continue editing assigned goals.

Planning is a solo effort. Concurrent planners on the same planning branch will
cause boss-number collisions and merge conflicts, and CAC does not try to
prevent this. Multi-planner coordination may be addressed in a future release.

The planning branch also hosts archiving. Once a completed or abandoned
campaign has merged into `main` and been pulled into `planning`, archive the
campaign there; archiving a campaign also archives its currently assigned boss
(see "Lifecycle and outcome"). Planning work, including archiving, reaches
`main` through the same PR or merge.

Campaign lifecycle operations update the linked boss themselves, in core, as part
of the same operation:

- `boss_assign_campaign` sets the boss's campaign link (on the assignment branch).
- Campaign completion sets the boss to `vanquished` (on the execution branch).
- Campaign abandonment releases the boss's campaign link (on the execution branch).
- Campaign reactivation returns the boss from `vanquished` to `available`.
- Campaign archiving sets the boss's `archived` flag (on planning).

These operations change only the boss's frontmatter, never its body. This
coupling keeps the two records consistent without giving campaign management any
way to edit a boss's aspirational content, and there is no separate public
operation for setting `vanquished`. Apply the same rollback rules as assignment
(see "Promotion contract") when one half of a coupled update fails. These are
lifecycle exceptions, not general editing rights. Execution branches do not edit
boss design content.

Assign the boss at draft campaign creation, before any encounter is created.
Encounter creation does not trigger assignment.

### Choosing the next number

Number allocation is a skill responsibility. Core endpoints do not allocate
numbers, scan branches, or require the numbered format; they accept the names
they are given under the existing name validation. Allocation done by skills
is not deterministic, but it is flexible and has proven easy in practice.
Projects already follow similar conventions through local agent instructions.

Skills should inspect existing records, including archived records, plus local
and known remote campaign branch names. For campaigns, choose one greater than
the highest known `c` number across these sources. A branch reserves its number
even if its campaign record has not yet been committed. Refresh remote refs
when available and disclose when the view is incomplete. Do not treat a network
failure as proof that no competing branch exists.

For encounters, choose one greater than the highest allocated `e` number within
that campaign, starting at `e001`. Existing encounter records, including retained
history, are the authority; each campaign has its own sequence. Parallel edits
within the same campaign still require coordination.

Boss numbers come from the single planning branch. Because planning is a solo
effort, boss allocation needs no cross-branch collision checks.

Skills perform a brief collision check at campaign creation, after pulling or
merging another branch into the campaign branch (or equivalent rebasing), and
before completing the campaign to prepare its PR. Repeat the last check after
reactivation and review fixes.

Check numeric IDs and names, reciprocal boss/campaign links, and encounter IDs
within their campaign. Different filenames sharing a numeric ID are collisions
even when Git merges cleanly. Two campaigns assigned to one boss also conflict.
The expected assignment/execution pair is not a duplicate allocation.

Resolve collisions manually, including any merge conflicts. Do not silently
renumber objects. Manual repair may require changing names, branch names, and
all affected references together; recheck before continuing dependent work.
This is an explicit exception to the ordinary recommendation against renaming.

Git discovery is best effort, not an atomic allocation service. Shared assignment
PRs and these checkpoints provide visibility without a mandatory registry,
central allocator, or distributed lock service. Occasional collisions and merge
conflicts are an accepted tradeoff for keeping developer friction low.

## Rumors: discoveries returned to planning

A campaign may optionally create a markdown rumors file on its execution branch.
Its location relative to the managed sourcebook root is
`bosses/rumors/cNNN-slug-name.md`, using the campaign's full canonical name.
There is one file per campaign, created only when useful; it needs no separate
number or identity scheme.

Rumors capture possible new goals, suggested boss changes, constraints, questions,
and other details discovered during implementation. They are mostly freeform:
no required headings, structured entries, per-note statuses, review gates, or
mandatory links. Engineers can organize the document however best preserves the
information. Capturing a rumor does not change the campaign's scope, modify a
boss, or automatically create future work.

The workflow is:

1. Create and revise the campaign's rumors file on its working branch as needed.
2. Include it in the completed campaign's implementation PR into `main`.
3. Pull the integrated records into `planning`.
4. On `planning`, freely edit and distill the rumors into new or updated eligible
   boss records, or leave them for later consideration. Assigned bosses retain
   their read-only protection; a rumor does not bypass it.

No explicit rumor-to-boss lineage is required. Git commits preserve what was
captured and how planning evolved it. Do not add conversion bookkeeping,
processed flags, mandatory acknowledgements, or a requirement to turn every
rumor into a boss. Planning engineers may rewrite, consolidate, retain, or remove
distilled notes as they see fit, with the history retained in Git.

Rumors are never archived. Once their content has been used to update bosses,
delete the file on planning; Git keeps the history. Archiving a campaign leaves
any remaining rumors file in place for planning to distill or delete. The intent
is to keep rumors fluid for developers.

Rumors are a separate kind of document nested beneath the bosses collection,
not boss records themselves. Boss listing, numbering, dependency resolution,
and candidate selection must exclude them. Their presence must not reserve a
boss number. Under the skills' guidance, execution branches edit only their
own rumors file, and general rumor editing and distillation belong on
`planning`. The endpoints themselves do not check the branch, and reads are
available wherever the file is present. Existing MCP/CLI-only content access still applies, using
simple document operations rather than imposing a structured rumor workflow.

## Domain model

| Object | Responsibility |
| --- | --- |
| Boss | Preserve a possible goal, its rationale, and prerequisites |
| Campaign | Organize the chosen effort to achieve that goal |
| Encounter | Plan, review, execute, and verify a concrete unit of work |
| Campaign rumors | Preserve freeform discoveries for later planning |

Proposed boss attributes:

| Attribute | Meaning |
| --- | --- |
| `name` | Unique numbered name, such as `b001-improve-planning` |
| `summary` | Short routing summary, with the existing 500-character limit |
| `status` | `proposed`, `available`, `withdrawn`, or `vanquished` (successfully completed) |
| `archived` | Flag set when archived, matching campaigns and encounters; status is left untouched and the record moves to the sourcebook's `archive/bosses` directory |
| `depends_on` | Direct prerequisite boss names |
| `campaign` | Current assigned campaign; absent before assignment or after an abandoned attempt is released |
| Audit attributes | Creation and update attribution/timestamps consistent with CAC |

The campaign receives an optional `boss` reference. Existing campaigns remain
valid without one; direct campaign creation remains supported. New promotions
create a new campaign rather than attach a boss to an existing campaign.

Use a markdown body with suggested headings: Goal, Rationale, Success Criteria,
Design Notes, and Open Questions. These guide useful capture without imposing
encounter-style fixed sections or review gates. An early idea can be incomplete.
Before promotion, the selecting agent and developer should establish a bounded
goal and an observable success condition.

The summary and body should be updated together so candidate discovery does not
present obsolete intent. No readiness checklist or numeric priority is required
for initial capture.

## Lifecycle and outcome

| Transition | Effect |
| --- | --- |
| Create | Start as `proposed`, with editable aspirations and relationships on planning |
| Make available | A planner deems the boss ready for a campaign |
| Update | Refine unassigned proposed/available bosses on planning; re-evaluate readiness after scope changes |
| Assign | Link one draft campaign to an available boss and lock its design; assignment is a relationship, not a `promoted` status |
| Withdraw | Set aside an unassigned, non-vanquished goal on planning |
| Vanquish | Campaign completion sets boss status to `vanquished`, its successful-completion status |
| Archive campaign | On planning, set the `archived` flag on the campaign and its currently assigned boss |
| Reactivate withdrawn boss | On planning, return `withdrawn` -> `proposed` for renewed consideration |
| Archive withdrawn boss | On planning, set the `archived` flag |

An assigned boss remains `available` with its campaign reference set until
completion; it is excluded from new assignments. This avoids inventing a new
assignment status. An unassigned available boss is planner-approved, but may
still be blocked by prerequisites. Availability and execution eligibility differ.

Boss lifecycle metadata must remain consistent with its linked campaign:

| Linked campaign status | Interpretation |
| --- | --- |
| `draft` | Selected; execution has not started |
| `open` | Being pursued |
| `paused` | Selected effort is paused |
| `completed` | Boss `vanquished`; satisfies dependencies once visible on planning (see "Dependencies and precedence") |
| `abandoned` | Release the current assignment and return the boss to available for another campaign |
| Missing or inconsistent link | Integrity problem requiring attention |

Campaign completion remains the developer-confirmed assertion that the goal has
been achieved. Creating or opening the campaign does not defeat the boss.
Campaign archiving happens on planning and must archive its currently assigned
boss too, preserving reference resolution. Because archiving is a flag rather
than a status, the boss keeps its status: an archived vanquished boss still
satisfies dependencies, while an archived withdrawn boss does not. Coordinate these
updates through supported operations, without changing frozen design notes.
An abandoned historical campaign whose assignment was released must not archive
or otherwise change a boss now available or assigned to a different campaign.

### Reactivation for PR feedback

Support `completed` -> `open` on the matching execution branch with a recorded
reason and normal approval for opening work. Preserve earlier completion and
postmortem entries; append the reactivation rather than erasing history. The
campaign body becomes editable while open, and completing it again appends a
new closing entry. Completion locks the body until explicit reactivation rather
than imposing an irreversible lock.

The boss remains linked and its design frozen. Reactivation returns the boss
from `vanquished` to `available`, still linked, until the campaign completes again. Completed encounters remain
historical records; create new encounters with continuing sequence numbers for
review fixes. Encounter reactivation is not implied. Complete and verify the
campaign again before merging its implementation PR.

Reactivation exists only for review feedback before merge. Archived campaigns
cannot be reactivated. Problems found after the implementation has merged get a
new campaign, against a new or split boss.

On the reactivated branch the boss is not locally defeated until completion
again. Other branches see their synchronized records. Local completion does not
prove implementation has merged into `main`; prerequisite discovery must make
that distinction visible.

Planning manages bosses and their supporting rumors, not campaigns. Its only
campaign operation is archiving integrated terminal campaigns. There is no
`abandoned` boss state: use `withdrawn`. Withdrawn bosses can be archived on
planning or returned to `proposed`, preserving history and requiring a fresh
planner readiness decision before availability. Returning a boss to proposed
does not reopen or change any campaign.

A boss must be unassigned to be withdrawn, and the endpoint rejects withdrawal
of a linked or vanquished boss. This is a rule about the boss's state, not about
branches. To give up on an assigned goal, abandon its campaign first (which
releases the boss), then withdraw the boss on planning. Withdrawal never
abandons a campaign or releases an assignment.

CAC provides no boss deletion operation; withdrawal and archiving retire goals.
If a developer really wants a boss gone (for example, one created by mistake),
they can remove the file themselves and rebuild the search index. As with any
manual change to the sourcebook, this is the developer's choice, outside the
MCP/CLI workflow, and not something the coding assistant does on its own.

When an assigned campaign is abandoned, campaign management removes the boss's
current campaign reference and makes the boss available for a new campaign and
its encounters. Keep the abandoned campaign's boss reference as historical
context; it no longer represents a reciprocal current assignment. New assignment
checks distinguish such historical attempts from competing current assignments.
Synchronize this release into the merge target and planning through normal Git
workflows before relying on the newly available goal across checkouts.

## Dependencies and precedence

For the first release, `depends_on` is optional and may be empty. Its entries
reference bosses and express hard prerequisites. The intended prerequisite is a
completed implementation integrated into the merge target.

Candidate discovery uses a simple rule: a prerequisite is satisfied when its
boss's recorded status is `vanquished`, whether or not it is archived. This
matches the intended meaning because of how the workflow is shaped. Candidate
selection happens on `planning`, and `planning` receives campaign records only
by synchronizing from `main`. A campaign reaches `main` only after it is
completed and merged, so a `vanquished` boss visible on `planning` has already
been integrated. Off planning (for example, on an execution branch with a
locally completed campaign), the same rule applies, and skills note that the
result reflects local state rather than `main`. Optional post-merge automated
tests can support the developer's process but are not required by the framework.

No starting condition is required when dependencies are empty. Unselected,
withdrawn, paused, abandoned, or missing prerequisites remain unsatisfied; none
are silently treated as complete.

Dependency changes must reject self-dependencies, duplicate edges, unknown
targets, and cycles. Reject new dependencies on withdrawn bosses. An existing
dependency on a boss that is later withdrawn remains visible as a blocker.

Keep preference statements such as "prefer this after documentation" in design
notes initially. A separate soft-precedence relationship may be useful later,
but it must not silently acquire the blocking semantics of `depends_on`.

Eligibility and recommendation are different:

- **Eligible:** available, unassigned, with all prerequisites satisfied and no integrity errors.
- **Blocked:** available and unassigned, with unsatisfied prerequisites or broken references.
- **Not ready:** proposed; not yet deemed ready by a planner.
- **Selected/retired:** assigned, withdrawn, vanquished, or flagged archived; excluded from new-work candidates.

Eligibility does not certify that the design is sufficiently understood, rank
business value, or authorize execution. Return explicit prerequisite names,
linked campaign statuses, and reasons so an agent can explain its recommendation.
Use deterministic ordering for reproducibility; ordering is not a priority score.

## Splitting a boss

On planning, split an oversized unassigned boss by creating one or more new
bosses and reducing the original boss's scope. Keep its original identity; do
not require withdrawal or replacement lineage. Re-evaluate readiness for the
smaller goals. Assigned bosses remain frozen; record follow-up ideas as rumors.

Do not automatically redirect dependents: a dependent may need one replacement,
several, or a different outcome entirely. Report affected dependents and require
explicit changes while those records remain editable. Splitting alone does not
satisfy any prerequisites.

Initially this can be a guided sequence of existing boss operations rather than a
dedicated split command. Preserve rationale in the edited notes and Git history.

Scope changes may invalidate assumptions of dependent bosses, including frozen
assigned ones. Accept this as a planning risk: the planning skill should inspect
affected goals, flag inconsistencies, and work with the developer to reconcile
them. Do not add mandatory snapshots, automatic dependency rewrites, or extra
scope-change locks to solve this risk mechanically.

## Promotion contract

A proposed assignment operation `boss_assign_campaign(name, campaign_name, body)` should:

1. Confirm the boss is available, eligible, and has no campaign link.
2. Confirm the requested campaign name is unused, including archived
   campaigns. The endpoint does not check the branch. Before calling it, the
   skill confirms that the numeric ID is unused and that the current branch is
   the matching assignment branch. The expected assignment/execution branch
   pair is not a collision.
3. Create a draft campaign with deliberately crafted tactical content addressing
   the boss's aspirational requirements and success conditions, plus its origin
   reference. Do not copy the boss body as the campaign plan.
4. Set the boss's campaign reference, retaining its notes,
   summary, and dependency snapshot unchanged.
5. Return both records' identifiers and the resulting campaign status.

Promotion does not open the campaign, create encounters, bypass lore review, or
authorize execution. Promotion registers the draft on its assignment branch;
opening happens on its execution branch after registration. Another developer's
campaign can remain active on its own execution branch.

If assignment fails, undo the assignment changes in each file, preserving any
pre-existing unrelated content, and ask the developer how to resolve the failure.
Remove only the newly created draft if needed to restore the pre-assignment
state. Do not publish a partial assignment or silently retry a different mapping.
If rollback itself fails, report exactly what remains inconsistent and stop for
developer guidance. A repeat request for the same successful assignment returns
the existing result; a different campaign target must fail.

These guarantees apply to one local store. Independent clones can each promote
their own copy. Assignment PRs, skill collision checks, synchronization, and
manual repair provide cross-branch coordination without a required central service.

If an assignment PR is rejected, the boss on `main` and `planning` was never
frozen: the rejected PR carried the boss's campaign link and the draft campaign
with it. Cleanup is limited to the assignment branch and any execution branch
created from it. A rejected PR can leave several different situations, so the
skill guides the developer through this cleanup manually rather than performing
a fixed procedure.

Similarly, an assignment can merge and the team can then decide not to pursue
the campaign before any execution branch exists. Resolve this during planning or
with a small clean-up PR that abandons the draft and releases the boss. Cases
like this will always need some manual judgment.

## Agent discovery workflow

1. Orient using normal project context, the current branch, and its active campaign.
2. If there is an open campaign, continue its existing work workflow.
3. Otherwise, surface paused campaigns and existing draft campaigns alongside
   eligible bosses, avoiding duplicate initiatives or forgotten commitments.
4. Fetch candidate summaries and blockers on demand, then hydrate only the boss
   notes needed to compare choices.
5. Recommend a goal with rationale and unresolved questions; the developer
   chooses whether to promote it.
6. Allocate the next campaign number and follow the assignment-PR workflow above,
   then draft and open the campaign on its execution branch using normal approval
   procedures.

Prime should include the current boss details: the boss linked to the active
campaign, so campaign scope stays aligned with what planning intended. Do not
append the full boss knowledgebase to every prime response. Discovery must
remain paged and bounded. A response should distinguish "no proposed
bosses" from "all proposed bosses are blocked" and provide a route to inspect
the blockers. No automatic promotion or automatic campaign opening is implied.

## Proposed interfaces and implementation surfaces

Names below are proposals, not available commands:

| MCP tool family | CLI equivalent | Purpose |
| --- | --- | --- |
| `boss_create`, `boss_get`, `boss_list`, `boss_update` | `cac boss create/get/list/update` | Capture and retrieve goals |
| `boss_assign_dependency`, `boss_unassign_dependency` | `cac boss assign-dependency/unassign-dependency` | Maintain prerequisites |
| `boss_candidates` | `cac boss candidates` | Paged summaries, eligibility, and blocker explanations, ordered by boss number |
| `boss_assign_campaign` | `cac boss assign-campaign` | Register a crafted draft campaign and freeze boss design |
| `boss_make_available` | `cac boss make-available` | Record planner readiness for assignment |
| `boss_withdraw` | `cac boss withdraw` | Set aside a goal on planning |
| `boss_reactivate` | `cac boss reactivate` | Return a withdrawn boss to proposed on planning |
| `campaign_reactivate` | `cac campaign reactivate` | Reopen a completed campaign with an attributed reason |

Provide equivalent CLI/MCP operations to list, read, create, replace, and remove
campaign rumors documents. Exact command names remain to be chosen. Preserve
arbitrary markdown and allow whole-document editing rather than requiring
structured note submission. Like every endpoint, these operations are
branch-agnostic; the skills apply the execution-branch and planning-branch
guidance described above.

Provide no boss deletion operation in the initial release; withdrawal and
archiving cover retirement, and developers can still remove files by hand and
reindex. Protect linked campaigns from deletion, and preserve reads through
archiving.
Do not allow generic metadata mutation to bypass lifecycle or link invariants.

Follow the existing architecture: domain behavior in `core`, thin CLI and MCP
wrappers with parity, shared configuration/status definitions, and packaged
templates. Proposed storage is markdown with frontmatter under a new managed
boss collection. All interaction remains MCP/CLI-only.

Include bosses in search with a distinct object type and documented handling of
terminal records. Extend response-budget and pagination behavior consistently.
Campaign reads should expose the origin boss without recursively embedding its
body. Resolve numbered short references alongside canonical names. External
tools need a project identity plus numbered object reference, rather than
machine-specific absolute paths. Endpoints add no Git or branch awareness. Skills
read branch context from the target project checkout, including linked
worktrees.

The search index under the managed sourcebook is gitignored and updated only by
CAC writes, so switching branches leaves it stale. Address this as part of the
search integration: either detect staleness automatically, or have the skills
rebuild the index after a branch switch.

Add a dedicated planning skill for bosses and rumor distillation, with packaged
Claude and Codex variants (working name: `world-planner`; final name chosen at
implementation, and added to the deployed skill set). Update campaign-manager for assignment, branch checks,
completion/reactivation, and collision checks. Update the canonical packaged
workflow reference with these procedures. Deployed skill copies are not authoring sources.

## Quality-of-life changes in this release

### CLI body files

Add `--body-file PATH` to every CLI command that accepts `--body`, including
new boss and rumors commands where applicable. This supports large markdown
bodies prepared in a temporary or sandbox file without shell argument-length
and quoting problems. The file is an input artifact, not a managed record;
the CLI still performs the actual content write through its normal core API.

Proposed input behavior:

- Accept either `--body` or `--body-file`, rejecting both together with a clear
  usage error rather than silently selecting one.
- Read the file as UTF-8, preserving markdown and newlines. Do not modify or
  remove the input file.
- Report missing files, directories supplied as files, unreadable files, and
  invalid encoding before mutating any record.
- Apply the same body validation and lifecycle rules as inline input. An empty
  file follows the command's existing empty-body semantics.
- Preserve existing defaults, editor behavior, and required-input rules when
  neither option is supplied. This is an additive input method.

Resolve the input in a shared CLI helper so commands behave consistently. Core
and MCP APIs continue receiving body text; they do not need local file-path
arguments. Document a file-based example in user guidance and CLI help.

### Codex hook scope

Change the packaged Codex guard hook to deny only `apply_patch` operations that
directly modify managed sourcebook content. Remove shell/Bash command denial
from the hook. Routine directory listings and viewing commands should no longer
be rejected because their text mentions the managed content directory.

The MCP/CLI-only instruction for managed content remains the project workflow;
this change narrows automated enforcement to reduce developer friction. It does
not authorize agents to use shell commands to bypass that instruction. Patches
to ordinary repository files, including documentation discussing sourcebook
paths, should be judged by their actual target paths rather than incidental
text in the patch body.

Implement this in the packaged hook template and corresponding deployment
configuration and tests, not by hand-editing deployed hook copies. Update
framework-owned guidance to describe the narrower hook accurately. The developer
redeploys through the existing bootstrap workflow; the coding assistant does not
run bootstrap or disable the current hook as part of authoring this design.

## Documentation deliverables

### Branching guide

Add `branching-guide.md` as a framework-owned reference describing planning and
campaign branches. Author the packaged source alongside the existing reference
guides and expose it through the normal docs interfaces; provide a discoverable
link from public getting-started documentation. It must cover:

- Creating `planning` from `main`, synchronizing before boss edits, publishing
  bosses before assignment, and distilling integrated campaign rumors.
- Numbered boss, campaign, and encounter names and short references.
- Assignment branches and their registration PRs, followed by execution branches.
- Branch-scoped activation, no active campaign on main, and planning's boss-only
  responsibilities with the narrow assignment/lifecycle metadata exceptions.
- The three skill collision checkpoints and explicit manual conflict resolution.
- Campaign completion before implementation PRs and reactivation for review fixes.
- A concrete end-to-end example, plus guidance for independent clones/worktrees
  and existing projects adopting the new workflow.

Keep the branching guide consistent with the canonical workflow reference and
skills. Explain branch usage and rationale without creating a second conflicting
definition of lifecycle rules.

### Migration guide and local agent instructions

Update the migration guide for adoption from prior library versions. The guide
must explain the changed workflow explicitly enough that an agent using the
older library and its deployed skills can identify and intelligently update
the project's local `CLAUDE.md` and/or `AGENTS.md`.

Do not rely on an older installed library exposing the newly packaged guide:
document how to obtain the target release's migration instructions before or
during upgrade. State source and target versions when release numbering is set,
prerequisites, the supported upgrade sequence, and how to verify the result.

Include a concise old-to-new instruction mapping covering planning ownership,
boss readiness and assignment, campaign branch activation, numbering/collisions,
rumors, completion/reactivation, and the narrower Codex hook. Explain where to
link the branching guide and dedicated planning skill from local instructions.
Preserve the MCP/CLI-only workflow and the developer-only bootstrap restriction.

Local instruction files are user-owned. Read the existing files, identify
obsolete CAC guidance, and propose targeted edits preserving unrelated project
rules, local customizations, and existing import relationships. Update only the
files actually present; if both exist and one imports the other, keep shared
guidance in its established source rather than duplicating it. Do not blindly
replace either file or require their contents to match a template.

Distinguish migration of local instructions from redeployment of framework-owned
skills/hooks and any managed-record migration. Honor the existing migration
approval and guardrail procedures where applicable; do not assume the older
library understands new statuses or that bootstrap performs record migration.
Document compatibility for historical unnumbered records and how in-flight work
is handled. Finish with checks that local instructions, deployed skills, hook
behavior, and installed library describe the same workflow.

## Compatibility and release plan

Existing sourcebooks and campaigns must continue to load. A missing boss
collection means no bosses, not a broken installation; create it lazily through
approved operations. Do not infer bosses from historical campaigns or rewrite
existing goals automatically.

Preserve legacy unnumbered campaigns and encounters for historical reads without
automatically renaming them. During migration, inventory open/in-progress and
paused campaigns, notify the developer of naming/branch/workflow mismatches, and
help update those campaigns as part of adoption. Propose targeted repairs with
the developer rather than failing the sourcebook or requiring wholesale migration
before work can continue. Branch guidance is skill-based; it must not strand
legacy records behind new mechanical gates.

Assess schema-version requirements during implementation. If a version change
is needed, document the supported upgrade through the migration guide rather
than assuming bootstrap migrates an existing sourcebook. Release numbering is
still to be chosen; "Boss Edition" is the feature's working title.

Suggested implementation sequence:

1. Decide the items listed under "Remaining implementation details".
2. Implement core storage, validation, dependencies, and candidate explanations.
3. Implement promotion, campaign references, and deletion/archive safeguards.
4. Expose equivalent CLI/MCP interfaces and integrate bounded search/discovery.
5. Update skills, workflow reference, user documentation, and migration guidance.
6. Deliver CLI body-file support and the narrower Codex hook, with updated help,
   deployment guidance, and focused regression checks.
7. Publish the branching guide and version-specific migration guidance, including
   targeted updates to user-owned local agent instruction files.

This sequence is planning guidance, not a set of approved encounters.

## Verification expectations

Implementation encounters should cover:

- Planner readiness, optional dependencies, assignment locking, and lifecycle synchronization.
- Graph validation, branching dependencies, and deterministic candidate results.
- Blockers for unpromoted, paused, abandoned, withdrawn, and missing prerequisites.
- Recorded completion/archive outcomes and clear limits of manual integration checks.
- Abandoned assignment release, reassignment, historical attempt references,
  and no boss archive side effects from an obsolete abandoned campaign.
- Assignment links, deliberately crafted campaign content, retry behavior, name
  collisions, rollback in both files, and developer escalation on failure.
- Protected campaign deletion and visible diagnostics for damaged links.
- Scope reduction of the original boss plus new bosses, without forced withdrawal.
- Coupled campaign/boss archiving via the `archived` flag, the move into
  `archive/bosses`, retained status, and planning reactivation.
- Campaign operations change only boss frontmatter and never the boss body;
  rollback when one half of a coupled update fails.
- Withdrawal rejected for linked or vanquished bosses; no boss deletion
  operation exposed; archived campaigns cannot be reactivated.
- Prime includes the active campaign's boss within the response budget.
- Compatibility with sourcebooks lacking bosses and campaigns lacking boss links.
- CLI/MCP parity, literal markdown output, pagination, and response budgets.
- Search visibility, packaged templates, and documented agent workflows.
- Packaged branching-guide discovery and consistency with skills/workflow docs;
  migration guidance accessible from an older installation, with targeted
  CLAUDE/AGENTS updates preserving project rules and import relationships.
- Body-file support across all body-accepting CLI commands, mutual exclusion,
  large/multiline markdown, paths with spaces, error handling before writes,
  and unchanged inline/editor behavior.
- Codex hook regression checks: shell calls are not denied by this hook,
  direct managed-content apply_patch edits remain denied, and ordinary-file
  patches mentioning managed paths remain permitted. Check deployment wiring
  as well as hook logic.
- Optional rumors documents, literal freeform markdown round trips, editing on
  the matching execution branch and on planning, and exclusion from boss
  enumeration and number allocation. Distillation requires no lineage metadata.
- Skill guidance for planning-only boss management and its narrow lifecycle
  exceptions, draft registration on main without activation, and
  assignment/execution branch pairs.
- Skill collision checks at creation, branch integration, and pre-completion;
  duplicate IDs after clean Git merges; explicit manual repair guidance.
- Completed campaign reactivation, preserved closing entries, new follow-up
  encounters, boss immutability, and repeated completion for implementation PRs.
- Three-digit formatting, transition to four digits, numeric ordering, and
  project-wide campaign IDs versus campaign-local encounter IDs.
- Short-reference resolution, duplicate numeric IDs, archived number retention,
  local/remote branch discovery, and incomplete remote visibility.
- Endpoints behave identically on every branch (no branch-dependent validation).
  Skill guidance covers branch-scoped activation, no active campaign on `main`,
  independent campaign worktrees, unrelated branches, detached HEAD,
  custom branch names, local merges without PRs, and legacy in-flight campaigns.
- Search results after branch switches (staleness detection or skill-driven rebuild).

Run narrow relevant tests first, followed by the repository's full pytest and
ruff checks as required for implementation encounter verification. This design
draft alone does not require runtime changes or a new test suite.

## Remaining implementation details

- Finalize the `merge_target_branch` and `planning_branch` attribute names and
  how world tools expose them.
- Define archive restoration separately from the agreed withdrawn -> proposed
  path if restoration is needed in this release.
- Decide whether editing an `available` boss's scope automatically returns it to
  `proposed`, or whether re-evaluating readiness is skill guidance only.
- Choose the planning skill's final name (working name: `world-planner`).
- Choose how the search index handles branch switches: automatic staleness
  detection or skill-driven rebuild.
- Define exactly which boss fields prime includes for the active campaign's boss
  while staying within the response budget.
- Write practical skill examples for cleaning up rejected assignment PRs,
  abandoning registered drafts that were never started, resolving legacy
  records, and manual pre-planning integration checks.

The independent review's workflow questions are resolved through the guidance
above. Implementation should favor assistant/developer reconciliation over new
mechanical enforcement and report the limits of locally observed Git state.

CI validation remains entirely the consuming developer's choice. CAC skills
carry the agreed merge-policy checks; this design does not require CI enforcement.

Messaging-framework selection, executor supervision, and distributed claims
remain separate from this feature's acceptance. Concurrent execution is enabled
through separate campaign branches; coordinating those executors remains external.
