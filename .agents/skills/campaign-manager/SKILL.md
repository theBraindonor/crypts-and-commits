---
name: campaign-manager
description: Select goals into tactical campaigns, manage campaign execution and review fixes, and draft, independently review, execute, and close encounters with the required developer approvals.
---

# Campaign Manager

Own tactical commitment and execution. world-planner owns goal planning/readiness,
roadmap adoption, integrated rumor distillation and planning-side archival;
world-manager owns static context and the disclosure ladder. Use connected
crypts-and-commits MCP tools first, cac CLI only when unavailable. Managed records
are MCP/CLI-only, never direct filesystem inspection/repair. Missing bootstrap
and stale index recovery are developer-only; never run bootstrap/index rebuild,
disable guardrails, or edit deployed skill copies.

## Orient and reconcile the branch

For worked Git examples, read docs_get("branching-guide") /
cac docs get branching-guide. For adoption from older installations and targeted
local instruction updates, use docs_get("migration-guide") /
cac docs get migration-guide; workflow remains the procedural authority.

Start with prime_get / cac prime get and world-manager's disclosure ladder.
Use active_boss_names, active_bosses and active_boss_diagnostics for all selected
goals. Hydrate missing/truncated bodies and integrity diagnostics; never choose
a first-boss alias or treat broken membership as bossless. Encounter lists remain
on demand. Full-text index_search can find encounter text; it is not a dedicated
encounter graph/discovery API or a complete retained-allocation inventory.

Do not read the workflow guide or tool reference during routine orientation.
When a procedural question arises (configured planning/merge-target branches,
numbering, collision checkpoints, reconciliation), read docs_get("workflow") /
cac docs get workflow and use its "Agent planning and campaign workflow" section;
for lifecycle guards use its Campaign, Encounter and Bosses sections. For an exact
argument, result shape, error or budget, read docs_get("tool-reference") /
cac docs get tool-reference. Check Git branch/worktree,
dirty changes and detached HEAD before mutations. Explain mismatches and reconcile
without silently switching/overwriting; endpoints remain branch-agnostic.
Use existing authorization without repeat prompts. Invoking this skill does not
authorize publication, pushing/merging, destructive cleanup, or messages to others.

## Allocate, select, and register

1. Inventory every campaign_list(include_archived=True) page / cac campaign list
   --include-archived [--cursor TOKEN], plus known local/remote campaign branch
   names. A branch reserves its c number without a committed record; the matching
   cNNN-slug-assignment/cNNN-slug pair counts once. Choose numeric max+1, 001..999
   then 1000, never lexical/time/search order or a partial page. Disclose missing
   remote refresh/integration evidence; do not infer no collision from offline refs.
2. For developer-selected goals, hydrate boss_get and boss_candidates /
   cac boss get / cac boss candidates. Confirm every goal available, unassigned,
   eligible and graph/link-consistent. Order is not business priority or approval.
   Selecting a prerequisite with its incomplete dependent does not satisfy it.
   If goals need refinement, hand back to world-planner rather than editing frozen
   design or inventing eligibility. Roadmap provenance is an original snapshot.
3. Craft tactical content addressing all selected goals and success conditions.
   Create the assignment branch from synchronized merge target under project Git
   policy; campaign_create(name,body,bosses=[...]) registers the draft and links.
   boss_assign_campaign(name,campaign_name,body) is the single-goal convenience.
   Exact single-goal retries preserve an existing group's membership/tactics.
   Inspect atomic/recovery errors; never publish a partial assignment.
4. Integrate the assignment registration before execution through the project's
   PR/direct-merge process. Create cNNN-slug from accepted registration/merge target;
   if starting from the assignment branch, reconcile accepted registration first.
   A bossless campaign can skip registration and start on cNNN-slug with the same
   allocation checks. Selection does not open a campaign or create encounters.
5. Open only with authorization on the matching execution branch. Under the
   recommended workflow main/planning have no open campaign; paused work remains
   on execution. These are skill guidance, not endpoint gates or mandatory CI/PR
   hosting. Custom configured branch names apply.

Check logical collisions at creation, after integrating another branch (pull,
merge/rebase), and before completion for implementation integration; repeat after
review fixes. Inspect numeric IDs/names, encounter IDs within this campaign, and
reciprocal ownership for every boss. A clean Git merge can still contain logical
collisions. Reconcile manually, not by silent renumbering/branch deletion or direct
managed-file edits. Existing unnumbered history remains valid.

## Campaign operations

| Intent | MCP | CLI fallback |
| --- | --- | --- |
| Read | campaign_get(name) | cac campaign get NAME |
| List with status/identities | campaign_list(cursor,include_archived=False) | cac campaign list [--include-archived] [--cursor TOKEN] |
| Create tactical draft | campaign_create(name,body,bosses=None) | cac campaign create NAME [--boss REF ...] --body-file PATH |
| Single-goal selection | boss_assign_campaign(name,campaign_name,body) | cac boss assign-campaign BOSS CAMPAIGN --body-file PATH |
| Replace entire draft membership | campaign_set_bosses(name,bosses,message) | cac campaign set-bosses NAME [--boss REF ...] --message REASON |
| Edit tactics | campaign_update(name,body) | cac campaign update NAME --body-file PATH |
| Open/pause | campaign_open / campaign_pause | cac campaign open / pause NAME |
| Complete/abandon | campaign_complete / campaign_abandon | cac campaign complete / abandon NAME --message TEXT |
| Reopen for pre-merge fixes | campaign_reactivate(name,message) | cac campaign reactivate NAME --message REASON |
| Delete permitted bossless draft/history | campaign_delete(name) | cac campaign delete NAME |
| Archive integrated terminal history | campaign_archive(name) | cac campaign archive NAME |

MCP body arguments are strings. CLI --body and --body-file conflict; absent both,
editor behavior applies. Repeat --boss per member; omitted bosses creates bossless,
and no --boss on set-bosses clears the set. Draft replacement requires a reason
and valid reciprocal retained members; same-set requests are read-only. Membership
locks after opening, including reactivation. Assigned boss designs remain frozen;
campaign body text cannot change links. Zero/one/many goals have no primary boss.

Only one campaign can be open in the checkout. Pause/complete/abandon fail with
open encounters; archive also requires every encounter completed/abandoned.
Completion needs a postmortem and achieves every selected goal. Abandonment
needs a reason, releases all current boss links and retains historical membership.
Closed bodies lock; campaign_reactivate with a reason reopens only unarchived
completed campaigns for pre-merge review fixes. Keep membership and earlier Logs,
draft new follow-up encounters (completed encounters never reopen), verify and
recomplete before integration. Post-merge new scope goes back to planning.
No campaign completion/push/merge is implied by completing one encounter.

Deletion is not unconditional: linked/historical memberships, reverse boss claims
and archived state are protected. MCP has no interactive deletion prompt; CLI
can prompt or accept --yes, without bypassing core guards. Do not use deletion
as a rollback/renumber shortcut. world-planner archives integrated terminal history
on synchronized planning: current bosses move; released/reassigned goals and
rumors stay untouched.

## Discoveries and unusual handoffs

Use rumors_get/create/update/delete / cac rumors get/create/update/delete with
explicit campaign context (or active fallback); Markdown is freeform, one document
per campaign, no frontmatter/categories. MCP get can page by cursor. CLI writes
use --campaign REF with --body/--body-file; MCP receives body strings. Capture
follow-ups without editing assigned bosses or expanding execution scope. Integrated
rumors are distilled by world-planner; deletion is deliberate, never automatic.

For rejected registration, establish whether it integrated and inspect visible
assignment/execution branches; revise or explicitly abandon, retain useful context
and number reservations. Never publish rejection as acceptance or auto-delete.
For an accepted draft cancelled before execution, abandon with reason on its
execution branch, integrate cleanup and synchronize planning. For legacy open
unnumbered work, inspect encounters/local guidance and agree a matching execution
branch, finishing/abandoning open encounters before pausing/closing; preserve
history instead of inventing bosses or bulk renaming. Follow workflow's "Reconciliation examples".
Remote/integration uncertainty and failed recovery need explicit reconciliation.

## Encounters

Before choosing the next e number, finish every encounter_list(campaign=...,include_archived=True)
page / cac encounter list --campaign REF --include-archived [--cursor TOKEN].
Allocate numeric max+1 within that exact campaign, including retained history;
never reuse an ID, rely on update order, or silently resolve duplicate numeric IDs.
Existing canonical/short refs accept archived records; missing/ambiguous context
requires clarification, not guessing. No active campaign means pass campaign
explicitly rather than opening one merely to inspect history.


An encounter is a concrete unit of work within a campaign, in one of two `kind`s, fixed at creation and never changed afterward:

- **`scripted`** (the default) — a plan the agent is expected to execute, with `Requirements`, `Rationale`, `Plan`, and `Verification` sections in its body.
- **`unscripted`** — a record of manual work the developer or the agent already did outside the plan-first flow (direct edits, quick fixes, exploratory changes), captured after the fact so a later session can recover the intent behind it. Only `Requirements` (what was done) and `Rationale` (why) apply — there is no `Plan` or `Verification` to write. Use this kind when asked to record or document a change that's already been made, rather than to plan one.

Both kinds go through the identical status lifecycle below, including the independent-reviewer gate and the three explicit user gates — see "Encounter Lifecycle" for where the two kinds' handling diverges.

### Choosing the campaign

The campaign is **optional** on every encounter tool: when omitted, it defaults to the currently **active** (the single `open`) campaign. Since normal work happens inside the open campaign, you usually don't pass a campaign at all. Pass `campaign` only to act on a *different* campaign.

- If no campaign is open and you don't pass `campaign`, the call fails asking you to open a campaign or pass one explicitly.
- The **mutating** tools (`encounter_create`, `encounter_update`, `encounter_delete`, `encounter_review`, `encounter_open`, `encounter_record_message`, `encounter_complete`, `encounter_abandon`, `encounter_assign_region`, `encounter_unassign_region`, `encounter_assign_dependency`, `encounter_unassign_dependency`) refuse a `campaign` that is `completed` or `abandoned` — you cannot change encounters in a closed campaign.
- The **read** tools (`encounter_get`, `encounter_list`, `encounter_order`) accept any existing campaign, including `completed`/`abandoned` ones, so past work stays inspectable.

In the tool forms below, `campaign` is shown explicitly, but omit it to use the active campaign.

- `encounter_list(campaign, cursor, include_archived=False)` — list encounter names within a campaign, ordered oldest-updated first (ascending by `updated_on`). CLI fallback: `cac encounter list --help`.
- `encounter_order(campaign)` — show every campaign encounter in deterministic dependency order, with status and direct dependencies. CLI fallback: `cac encounter order --help`.
- `encounter_get(name, campaign)` — show an encounter's frontmatter (`status`, `kind`, `regions`) and body. CLI fallback: `cac encounter get --help`.
- `encounter_create(name, body, campaign, kind)` — create a new encounter. `kind` is optional, defaulting to `scripted`; pass `"unscripted"` to record already-done manual work instead. The campaign must already exist and not be completed/abandoned. CLI fallback: `cac encounter create --help` (`--kind`/`-k`).
- `encounter_update(name, body, campaign)` — replace an encounter's body. Only works while status is `draft`. CLI fallback: `cac encounter update --help`.
- `encounter_review(name, message, campaign)` — move `draft` → `reviewed` after a lore review. Requires at least one region already assigned. Message is required and permanently locks the content. CLI fallback: `cac encounter review --help`.
- `encounter_open(name, campaign, message)` — move `reviewed` → `open` and begin execution. Message is optional. CLI fallback: `cac encounter open --help`.
- `encounter_record_message(name, message, campaign)` — append a note without changing status. Works while `reviewed` or `open`. CLI fallback: `cac encounter record-message --help`.
- `encounter_complete(name, campaign, message)` — move `open` → `completed` once verification passes. Message is optional. CLI fallback: `cac encounter complete --help`.
- `encounter_abandon(name, message, campaign)` — move `draft`, `reviewed`, or `open` → `abandoned`. Not available once `completed`. Message is required. CLI fallback: `cac encounter abandon --help`.
- `encounter_assign_region(name, region, campaign)` / `encounter_unassign_region(name, region, campaign)` — an encounter may be assigned to one or more regions. This link is recorded only on the encounter. Only permitted while `draft`. CLI fallback: `cac encounter assign-region --help` / `cac encounter unassign-region --help`.
- `encounter_assign_dependency(name, dependency, campaign)` / `encounter_unassign_dependency(name, dependency, campaign)` — change direct prerequisites while the dependent encounter is `draft`. CLI fallback: `cac encounter assign-dependency --help` / `cac encounter unassign-dependency --help`.
- `encounter_delete(name, campaign)` — remove an encounter only in a mutable campaign and while no other encounter depends on it. CLI fallback: `cac encounter delete --help` (the CLI additionally supports a `--yes`/`-y` confirmation skip; the MCP tool always deletes without prompting).

## Encounter Lifecycle

**`draft`** — the encounter is being documented. For a `scripted` encounter, write the `Requirements`, `Rationale`, and `Plan` sections; leave `Verification` describing how the work will be checked once it's done. For an `unscripted` encounter, write only `Requirements` (what was done) and `Rationale` (why) — there is no `Plan`/`Verification` to write, and the template created by `encounter_create(..., kind="unscripted")` doesn't include those headings. This is the only status in which `encounter_update` can replace the body. Also assign at least one region (`encounter_assign_region`) before requesting review — `encounter_review` will refuse to run without one, for either kind.

Region and dependency assignment are both only permitted while an encounter is `draft`, not after it moves to `reviewed`. Dependency assignments must reference a non-abandoned encounter in the same campaign and cannot introduce a self-dependency or cycle. An abandoned existing prerequisite remains an unsatisfied blocker until it is removed or replaced.

### Draft handoff

After drafting an encounter, give the developer a substantive report before asking for approval to launch the independent review. Make the report understandable on its own: the developer should be able to assess the proposed work and decide about review without opening the encounter. Include a link or reference to the full encounter for deeper inspection, and explain:

- **Identity and purpose:** encounter and campaign names, kind, `draft` status, the problem and its motivation, and the intended behavior or outcome. Describe a concrete before/after when it helps establish what success means.
- **Scope and approach:** affected areas and boundaries, the main implementation steps, and significant choices or tradeoffs with the reasons for them. Explain how the changes address the problem, rather than merely listing files or section titles.
- **Risks and decisions:** dependencies, important assumptions, risks, and unresolved questions that could affect scope or readiness. State when there are no unresolved decisions rather than inventing concerns.
- **Verification:** what will be checked, which outcomes demonstrate success, and any known limits of those checks.

For an `unscripted` encounter, explain the work already performed, why that approach was taken, available evidence, and remaining follow-up; do not invent a future Plan or Verification section. After revising a rejected or non-reviewable draft, explain which changes were actually made, why they address the findings, and which concerns remain before requesting renewed review approval. A draft report does not authorize a reviewer or execution.

Use several developed paragraphs or grouped bullets, scaling depth to the work's complexity and uncertainty. Explain why details matter; topic labels alone are insufficient. Do not impose a fixed word count or compress the report into a terse synopsis. Avoid padding, pasting the encounter, or repeating routine details that do not help the decision. Apply this same standard to the review report below.

**`draft` → `reviewed`** — this gate is performed by an **independent, fresh reviewer subagent**, never inline by the agent that authored the draft. An agent reviewing its own draft just re-checks it against the priors that produced it — a rubber stamp — so **do not review the encounter yourself**, whatever its `kind`.

1. **Get the user's explicit approval before spawning.** Do not launch the reviewer subagent just because an encounter reached `draft` — drafting is not itself approval to review. Stop and ask the user directly whether to proceed with the independent review, and wait for an explicit yes. This is a separate approval from the later `reviewed` → `open` approval, and it applies every time this step is reached, including a re-review after a **REJECT**/**NOT-REVIEWABLE** verdict and a follow-up `encounter_update` — not just the first pass over a fresh draft.
2. **Spawn a fresh reviewer.** Start an independent Codex subagent with no inherited conversation context. Never fork the authoring conversation, because a fork reproduces its context and bias. Hand the reviewer the [reviewer prompt template](#reviewer-subagent-prompt-template) below, filling in only the encounter and campaign names. Pass nothing else — no lore and no analysis of your own — so the review stays independent and also tests whether the encounter is self-contained enough to survive a context reset.
3. **Let it review within bounds.** The subagent primes the world/lore itself, checks the encounter's `Plan` (for `scripted`) or its `Requirements`/`Rationale` (for `unscripted`, standing in for a Plan since none exists) against applicable lore within a bounded reading surface, and returns findings, a verdict (**PASS-WITH-NOTES** / **REJECT** / **NOT-REVIEWABLE**), and a *proposed* review message. It does **not** run any mutating `cac` operation — the transition is scripted by this skill, per the verdict, as described next.
4. **Auto-transition on PASS-WITH-NOTES — no separate approval pause.** As soon as the reviewer returns a **PASS-WITH-NOTES** verdict, run `encounter_review(name, message)` yourself, from the main thread, immediately, with `message` set to the reviewer's proposed message — the message content is the reviewer's independent findings (its proposed message, verbatim or faithfully transcribed), never a self-summary. This permanently locks the encounter's body sections (Requirements/Rationale, plus Plan/Verification for `scripted`) — they can no longer be replaced with `encounter_update`, only appended to. Then relay the reviewer's findings, verdict, and the fact that the encounter is now `reviewed` to the user. This step's auto-transition has no separate approval pause of its own — the approval this gate requires already happened at step 1, before the reviewer was spawned.
5. **Feedback after the fact is a logged message, not a re-draft.** If the user has feedback or requested changes in response to a PASS-WITH-NOTES review, capture it with `encounter_record_message(name, message)` — do not attempt to reopen or re-draft the encounter's sections; the content is already locked, and `encounter_update` no longer applies once status has moved past `draft`.

On **REJECT** or **NOT-REVIEWABLE**, the auto-transition does not apply: do not run `encounter_review`, relay the reviewer's reasons to the user, revise the draft with `encounter_update` (still allowed while `draft`), and return to step 1 — get the user's explicit approval again — before spawning a fresh reviewer.

### Review handoff

After every independent review, give the developer a substantive report of the review and its practical impact, with the encounter's identity and a link or reference to its full record. Make the reasoning and next decision understandable without requiring the developer to read the encounter or raw reviewer output. Include:

- **Verdict and coverage:** what the reviewer examined, the applicable standards or areas checked, and the limits of the review. Distinguish plan review from verification of implemented work; do not imply coverage or evidence the reviewer did not report.
- **Findings and reasoning:** explain each material finding, its supporting evidence or rationale, and why it matters. Distinguish blockers, actionable notes, and flagged-but-unverified concerns, explicitly saying when none exist. Routine successful lore checks may be grouped; explain consequential checks rather than reproducing an exhaustive checklist.
- **Impact and response:** explain consequences for scope, approach, risks, verification, or readiness and how each actionable finding should be addressed. Distinguish proposed or recommended responses from revisions, recorded messages, or other actions actually taken. Identify remaining uncertainty and conditions that still need to be satisfied.
- **State and recommendation:** state the resulting encounter status and locking implications, and recommend **proceed** or **revise** with reasons tied to the findings. Identify the next approval needed; a passing verdict or recommendation never supplies that approval.

For **PASS-WITH-NOTES**, first perform the automatic `encounter_review` transition using the reviewer's proposed message as required above, then summarize the findings and impact. State that the encounter is `reviewed` and its sections are locked. Recommend proceeding when the notes can be handled under the approved plan; if they instead call for changes, explain the needed follow-up and record it with `encounter_record_message`, without attempting to replace locked sections. Ask for separate approval before opening; a recommendation is not approval.

For **REJECT** or **NOT-REVIEWABLE**, keep the encounter `draft`, summarize the review's reasons and impact, and recommend revision or clarification before a fresh review. After updating the draft, state which changes were actually made and which concerns remain, provide the revised draft summary, and ask for renewed review approval. Never imply that revisions alone have passed review. For `unscripted` encounters, explain the impact on the accuracy of the recorded work and any follow-up needed rather than implying that the recorded work awaits execution.

This conversational report supplements the independent reviewer's recorded message; do not replace or rewrite that message with your own report. Expand the explanation of material findings and their consequences as needed for the developer's decision, while preserving the reviewer's meaning and clearly identifying your own recommendations.

#### Reviewer subagent prompt template

Start an independent reviewer with no inherited conversation context. Replace `<ENCOUNTER>` and `<CAMPAIGN>`; do not add anything else to the prompt.

```
You are an independent reviewer for a Crypts and Commits (CAC) "encounter" — a
unit of work, either a plan for future work ('scripted' kind) or a record of
work already done outside the plan-first flow ('unscripted' kind). Review it
critically against the project's lore (standards and conventions). You did not
write this encounter; do not assume it is sound, and you are expected to
reject it if it does not hold up.

Encounter: <ENCOUNTER>
Campaign:  <CAMPAIGN>

Prime the context yourself — do not accept any summary of it. Use the
`world-manager` skill if it is available, or call these directly — MCP tools
first, falling back to the equivalent `cac` CLI command only if the MCP
server isn't available in your session:
- `world_get()` / `cac world get` — read the world summary.
- `encounter_get(name="<ENCOUNTER>", campaign="<CAMPAIGN>")` /
  `cac encounter get <ENCOUNTER> -c <CAMPAIGN>` — read the encounter and note
  its `kind` and its `regions`. For each region, `region_get(name=<region>)` /
  `cac region get <region>` for its documented `path`.
- `prime_applicable_lore(encounter="<ENCOUNTER>", campaign="<CAMPAIGN>")` /
  `cac prime applicable-lore <ENCOUNTER> -c <CAMPAIGN>` — resolve the exact
  enabled lore set that applies (world-assigned union every region this
  encounter is assigned to), returned as `name` + `summary` + `ref`. Then, for
  each `ref` returned, `lore_get(name=ref)` / `cac lore get <ref>` to hydrate
  its full body — the summary is only a routing signal; the body is what you
  check against.

If `kind` is `scripted`, check the `Plan` against each applicable lore item. If
`kind` is `unscripted`, there is no `Plan` or `Verification` — that is expected,
not a defect — so instead check the recorded `Requirements`/`Rationale` (the
intent behind work already done) against each applicable lore item.

Bounded reading surface — you may READ only:
- the encounter body,
- the applicable lore bodies (including any paths or globs the lore names),
- the assigned regions' documented `path`s,
- files the encounter explicitly names.
This bound is an instruction, not a technical sandbox — nothing stops you
reading elsewhere, so honor it deliberately. If you suspect a lore-relevant area
the encounter did NOT cite, FLAG it as unverifiable / possibly out of scope —
do not go read it or reverse-engineer intent from the wider repo. Catching such
sins of omission is valuable; chasing them is not.

Return this and nothing more:
1. Findings — for each applicable lore item, whether the encounter honors it, with
   any conflict or gap. List "flagged but unverified" concerns separately.
2. Verdict — exactly one of:
   - PASS-WITH-NOTES — reviewable and consistent with lore;
   - REJECT — the encounter conflicts with lore;
   - NOT-REVIEWABLE — too underspecified to review within the cited surface. For
     an `unscripted` encounter, an absent `Plan`/`Verification` is never itself
     grounds for this verdict — only vague or missing `Requirements`/`Rationale`
     content is.
3. A proposed one-paragraph `encounter_review` message string capturing your
   findings.

Do NOT run `encounter_review`, `encounter_open`, `encounter_update`, or any
other mutating `cac` operation (via MCP tool or CLI), and do not edit any
files. You are reviewing only.
```

**`reviewed` → `open`** — get explicit approval from the user, then run `encounter_open(name, message)`. A message is optional here. Opening fails until every direct dependency is `completed`, reporting all unsatisfied prerequisites and their statuses.

**`open`** — for a `scripted` encounter, execute the `Plan`. If the `Plan` or `Verification` needs to change based on what's found during implementation, do not attempt to edit them directly — use `encounter_record_message(name, message)` to record the deviation and why (also usable between `review` and `open`, i.e. while `reviewed`). For an `unscripted` encounter, the recorded work is already done — there's nothing to execute — so this is where the agent makes any follow-up changes the review's findings called for; if the review raised nothing actionable, there's nothing further to do here.

**`open` → `completed`** — for a `scripted` encounter, once all work is finished, run the steps described in `Verification`. For an `unscripted` encounter (no `Verification` section), confirm the recorded `Requirements`/`Rationale` are still accurate and any follow-up changes from `open` are done. Either way, confirm with the user before marking it complete — do not do this unilaterally — then run `encounter_complete(name, message)`. A message is optional.

**`draft`/`reviewed`/`open` → `abandoned`** — on request from the user, run `encounter_abandon(name, message)` (message required). Not available once an encounter is `completed`.
