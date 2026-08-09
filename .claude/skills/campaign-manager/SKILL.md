---
name: campaign-manager
description: Manage this project's active work-tracking loop - campaigns (long-running initiatives, like a Jira Epic) and encounters (concrete units of work, either 'scripted' with Requirements/Rationale/Plan/Verification sections or 'unscripted' with just Requirements/Rationale, recording manual work done outside the plan-first flow) - through the crypts-and-commits MCP server, falling back to the cac CLI when the server is unavailable. Use when asked to start a new initiative, move a campaign through its draft/open/paused/completed/abandoned lifecycle, plan a new unit of work, record already-done manual work, move an encounter through its draft/reviewed/open/completed/abandoned lifecycle, or assign an encounter to one or more regions.
allowed-tools: Bash(cac *), Task, mcp__crypts-and-commits
---

# Campaign Manager

Owns the project's active work-tracking loop: campaigns and the encounters within them. Work exclusively through the `crypts-and-commits` MCP server's tools when they are available for this session — never create, read, edit, move, or delete anything under `.sourcebook/` directly, whether with file tools or shell commands. Fall back to the `cac` CLI only when the MCP server is not connected for this session; the CLI covers the exact same operations (see each tool's "CLI fallback" pointer below).

If a command reports that the project hasn't been bootstrapped, stop and ask the developer to run `cac bootstrap init` themselves. Never run it on their behalf — this applies regardless of whether you'd otherwise reach for the MCP server or the CLI, since `bootstrap` is intentionally not exposed over MCP at all.

## Priming

Before starting any work in this loop — planning a new encounter, reviewing one, or resuming an open one — run the disclosure ladder's **Orient** step first: `mcp__crypts-and-commits__prime_get()`. That call (and the rest of the ladder — "Focus a task" / "Review a plan") is owned and documented by `world-manager`; see that skill for the full procedure. Its bundle already includes the active campaign's full body, so no separate campaign read is needed just to orient.

From there, this skill appends the active-loop context prime doesn't cover:

- `mcp__crypts-and-commits__encounter_list(campaign, cursor)` for the campaign's encounters — a separate, on-demand, paged call, never part of prime, since the encounter list is the one thing in this loop that grows without bound. CLI fallback: `cac encounter list --help`.

There is no encounter search yet — that capability is deferred (see `docs/encounter-search-design.md`). Don't reference or imply one exists; until it lands, `mcp__crypts-and-commits__encounter_list` plus reading names is the only way to find an encounter.

## Campaigns

A campaign is a long-running initiative, similar to an "Epic" in Jira-style work tracking (e.g. "Create the MVP", "Add Payment Processing", a version increment). It's expected to require many encounters, completed over time, before it's done.

- `mcp__crypts-and-commits__campaign_list(cursor)` — list all campaigns by name, with their current status. CLI fallback: `cac campaign list --help`.
- `mcp__crypts-and-commits__campaign_get(name)` — show a campaign's frontmatter (`status`, `created_on`/`created_by`/`updated_on`/`updated_by`) and body. CLI fallback: `cac campaign get --help`.
- `mcp__crypts-and-commits__campaign_create(name, body)` — create a new campaign, in `draft` status. CLI fallback: `cac campaign create --help`.
- `mcp__crypts-and-commits__campaign_update(name, body)` — replace a campaign's body. Fails once the campaign is `completed` or `abandoned` — its body is locked once its postmortem is recorded. CLI fallback: `cac campaign update --help`.
- `mcp__crypts-and-commits__campaign_open(name)` — move `draft` or `paused` → `open` and begin work. Only one campaign may be `open` at a time. CLI fallback: `cac campaign open --help`.
- `mcp__crypts-and-commits__campaign_pause(name)` — move `open` → `paused`. Fails if the campaign has an encounter that is currently `open`. CLI fallback: `cac campaign pause --help`.
- `mcp__crypts-and-commits__campaign_complete(name, message)` — move `open` or `paused` → `completed`. Fails if the campaign has an encounter that is currently `open`. The message is required — a postmortem, appended as a dated, attributed log entry on the campaign body. CLI fallback: `cac campaign complete --help`.
- `mcp__crypts-and-commits__campaign_abandon(name, message)` — move `draft`, `open`, or `paused` → `abandoned`. Not available once `completed`. Fails if the campaign has an encounter that is currently `open`. The message is required, recorded the same way as `complete`'s. CLI fallback: `cac campaign abandon --help`.
- `mcp__crypts-and-commits__campaign_delete(name)` — remove a campaign, unconditionally. CLI fallback: `cac campaign delete --help` (the CLI additionally supports a `--yes`/`-y` confirmation skip; the MCP tool always deletes without prompting).
- `mcp__crypts-and-commits__campaign_archive(name)` — archive a campaign and every one of its encounters, moving them into `.sourcebook/archive/` and setting `archived: true` on each. Requires the campaign to already be `completed`/`abandoned`, not already archived, and every one of its encounters to also be `completed`/`abandoned`. CLI fallback: `cac campaign archive --help`.

## Campaign Lifecycle

**`draft`** — the campaign was just created and hasn't started yet.

**`draft`/`paused` → `open`** — run `mcp__crypts-and-commits__campaign_open(name)`. Only one campaign may be `open` at a time; if another campaign is already `open`, this fails naming that campaign — pause or complete it first.

**`open` → `paused`** — run `mcp__crypts-and-commits__campaign_pause(name)` to set work aside without completing it. Fails, naming the offending encounter(s), if any encounter under the campaign is currently `open`; complete or abandon those encounters first (or wait for them to finish).

**`open`/`paused` → `completed`** — run `mcp__crypts-and-commits__campaign_complete(name, message)` once the initiative is done. Same open-encounter restriction as `pause`. The message is a required postmortem — a closing summary of what happened and what was learned — appended to the campaign body as a dated, attributed log entry. Once `completed`, the campaign's body is locked: `mcp__crypts-and-commits__campaign_update` will fail, since the postmortem is meant to be that campaign's closing record.

**`draft`/`open`/`paused` → `abandoned`** — run `mcp__crypts-and-commits__campaign_abandon(name, message)` to record why the initiative is being called off. Not available once `completed`. Same open-encounter restriction as `pause`, and the same required-postmortem, body-locking behavior as `complete`.

**`completed`/`abandoned` → archived** — once a campaign and *every one* of its encounters are `completed`/`abandoned` (a strictly broader check than the open-encounter guards above — `draft`/`reviewed` encounters block this too), run `mcp__crypts-and-commits__campaign_archive(name)` to move the campaign and all its encounters into `.sourcebook/archive/`, out of the way of active work. This does not change `status` — a `completed` campaign stays `completed`. `campaign_get`/`encounter_get` keep working unchanged afterward; `campaign_list`/`encounter_list`/`encounter_order` do not show archived content. CLI fallback: `cac campaign archive --help`.

## Encounters

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

- `mcp__crypts-and-commits__encounter_list(campaign, cursor)` — list encounter names within a campaign, ordered oldest-updated first (ascending by `updated_on`). CLI fallback: `cac encounter list --help`.
- `mcp__crypts-and-commits__encounter_order(campaign)` — show every campaign encounter in deterministic dependency order, with status and direct dependencies. CLI fallback: `cac encounter order --help`.
- `mcp__crypts-and-commits__encounter_get(name, campaign)` — show an encounter's frontmatter (`status`, `kind`, `regions`) and body. CLI fallback: `cac encounter get --help`.
- `mcp__crypts-and-commits__encounter_create(name, body, campaign, kind)` — create a new encounter. `kind` is optional, defaulting to `scripted`; pass `"unscripted"` to record already-done manual work instead. The campaign must already exist and not be completed/abandoned. CLI fallback: `cac encounter create --help` (`--kind`/`-k`).
- `mcp__crypts-and-commits__encounter_update(name, body, campaign)` — replace an encounter's body. Only works while status is `draft`. CLI fallback: `cac encounter update --help`.
- `mcp__crypts-and-commits__encounter_review(name, message, campaign)` — move `draft` → `reviewed` after a lore review. Requires at least one region already assigned. Message is required and permanently locks the content. CLI fallback: `cac encounter review --help`.
- `mcp__crypts-and-commits__encounter_open(name, campaign, message)` — move `reviewed` → `open` and begin execution. Message is optional. CLI fallback: `cac encounter open --help`.
- `mcp__crypts-and-commits__encounter_record_message(name, message, campaign)` — append a note without changing status. Works while `reviewed` or `open`. CLI fallback: `cac encounter record-message --help`.
- `mcp__crypts-and-commits__encounter_complete(name, campaign, message)` — move `open` → `completed` once verification passes. Message is optional. CLI fallback: `cac encounter complete --help`.
- `mcp__crypts-and-commits__encounter_abandon(name, message, campaign)` — move `draft`, `reviewed`, or `open` → `abandoned`. Not available once `completed`. Message is required. CLI fallback: `cac encounter abandon --help`.
- `mcp__crypts-and-commits__encounter_assign_region(name, region, campaign)` / `mcp__crypts-and-commits__encounter_unassign_region(name, region, campaign)` — an encounter may be assigned to one or more regions. This link is recorded only on the encounter. Only permitted while `draft`. CLI fallback: `cac encounter assign-region --help` / `cac encounter unassign-region --help`.
- `mcp__crypts-and-commits__encounter_assign_dependency(name, dependency, campaign)` / `mcp__crypts-and-commits__encounter_unassign_dependency(name, dependency, campaign)` — change direct prerequisites while the dependent encounter is `draft`. CLI fallback: `cac encounter assign-dependency --help` / `cac encounter unassign-dependency --help`.
- `mcp__crypts-and-commits__encounter_delete(name, campaign)` — remove an encounter, unconditionally. Fails while another encounter depends on it. CLI fallback: `cac encounter delete --help` (the CLI additionally supports a `--yes`/`-y` confirmation skip; the MCP tool always deletes without prompting).

## Encounter Lifecycle

**`draft`** — the encounter is being documented. For a `scripted` encounter, write the `Requirements`, `Rationale`, and `Plan` sections; leave `Verification` describing how the work will be checked once it's done. For an `unscripted` encounter, write only `Requirements` (what was done) and `Rationale` (why) — there is no `Plan`/`Verification` to write, and the template created by `encounter_create(..., kind="unscripted")` doesn't include those headings. This is the only status in which `mcp__crypts-and-commits__encounter_update` can replace the body. Also assign at least one region (`mcp__crypts-and-commits__encounter_assign_region`) before requesting review — `encounter_review` will refuse to run without one, for either kind.

Region and dependency assignment are both only permitted while an encounter is `draft`, not after it moves to `reviewed`. Dependency assignments must reference a non-abandoned encounter in the same campaign and cannot introduce a self-dependency or cycle. An abandoned existing prerequisite remains an unsatisfied blocker until it is removed or replaced.

**`draft` → `reviewed`** — this gate is performed by an **independent, fresh reviewer subagent**, never inline by the agent that authored the draft. An agent reviewing its own draft just re-checks it against the priors that produced it — a rubber stamp — so **do not review the encounter yourself**, whatever its `kind`.

1. **Get the user's explicit approval before spawning.** Do not launch the reviewer subagent just because an encounter reached `draft` — drafting is not itself approval to review. Stop and ask the user directly whether to proceed with the independent review, and wait for an explicit yes. This is a separate approval from the later `reviewed` → `open` approval, and it applies every time this step is reached, including a re-review after a **REJECT**/**NOT-REVIEWABLE** verdict and a follow-up `mcp__crypts-and-commits__encounter_update` — not just the first pass over a fresh draft.
2. **Spawn a fresh reviewer.** Use the `Task` tool with `subagent_type: "general-purpose"` — a fresh agent, **never a fork** (a fork inherits the authoring conversation and reproduces its bias). Hand it the [reviewer prompt template](#reviewer-subagent-prompt-template) below, filling in only the encounter and campaign names. Pass nothing else — no lore, no analysis of your own — so the review stays independent and also tests whether the encounter is self-contained enough to survive a context reset.
3. **Let it review within bounds.** The subagent primes the world/lore itself, checks the encounter's `Plan` (for `scripted`) or its `Requirements`/`Rationale` (for `unscripted`, standing in for a Plan since none exists) against applicable lore within a bounded reading surface, and returns findings, a verdict (**PASS-WITH-NOTES** / **REJECT** / **NOT-REVIEWABLE**), and a *proposed* review message. It does **not** run any mutating `cac` operation — the transition is scripted by this skill, per the verdict, as described next.
4. **Auto-transition on PASS-WITH-NOTES — no separate approval pause.** As soon as the reviewer returns a **PASS-WITH-NOTES** verdict, run `mcp__crypts-and-commits__encounter_review(name, message)` yourself, from the main thread, immediately, with `message` set to the reviewer's proposed message — the message content is the reviewer's independent findings (its proposed message, verbatim or faithfully transcribed), never a self-summary. This permanently locks the encounter's body sections (Requirements/Rationale, plus Plan/Verification for `scripted`) — they can no longer be replaced with `encounter_update`, only appended to. Then relay the reviewer's findings, verdict, and the fact that the encounter is now `reviewed` to the user. This step's auto-transition has no separate approval pause of its own — the approval this gate requires already happened at step 1, before the reviewer was spawned.
5. **Feedback after the fact is a logged message, not a re-draft.** If the user has feedback or requested changes in response to a PASS-WITH-NOTES review, capture it with `mcp__crypts-and-commits__encounter_record_message(name, message)` — do not attempt to reopen or re-draft the encounter's sections; the content is already locked, and `encounter_update` no longer applies once status has moved past `draft`.

On **REJECT** or **NOT-REVIEWABLE**, the auto-transition does not apply: do not run `mcp__crypts-and-commits__encounter_review`, relay the reviewer's reasons to the user, revise the draft with `mcp__crypts-and-commits__encounter_update` (still allowed while `draft`), and return to step 1 — get the user's explicit approval again — before spawning a fresh reviewer.

#### Reviewer subagent prompt template

Spawn with `subagent_type: "general-purpose"` (fresh, not a fork). Replace `<ENCOUNTER>` and `<CAMPAIGN>`; do not add anything else to the prompt.

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
- `mcp__crypts-and-commits__world_get()` / `cac world get` — read the world summary.
- `mcp__crypts-and-commits__encounter_get(name="<ENCOUNTER>", campaign="<CAMPAIGN>")` /
  `cac encounter get <ENCOUNTER> -c <CAMPAIGN>` — read the encounter and note
  its `kind` and its `regions`. For each region, `mcp__crypts-and-commits__region_get(name=<region>)` /
  `cac region get <region>` for its documented `path`.
- `mcp__crypts-and-commits__prime_applicable_lore(encounter="<ENCOUNTER>", campaign="<CAMPAIGN>")`
  / `cac prime applicable-lore <ENCOUNTER> -c <CAMPAIGN>` — resolve the exact
  enabled lore set that applies (world-assigned union every region this
  encounter is assigned to), returned as `name` + `summary` + `ref`. Then, for
  each `ref` returned, `mcp__crypts-and-commits__lore_get(name=ref)` / `cac lore get <ref>`
  to hydrate its full body — the summary is only a routing signal; the body
  is what you check against.

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

**`reviewed` → `open`** — get explicit approval from the user, then run `mcp__crypts-and-commits__encounter_open(name, message)`. A message is optional here. Opening fails until every direct dependency is `completed`, reporting all unsatisfied prerequisites and their statuses.

**`open`** — for a `scripted` encounter, execute the `Plan`. If the `Plan` or `Verification` needs to change based on what's found during implementation, do not attempt to edit them directly — use `mcp__crypts-and-commits__encounter_record_message(name, message)` to record the deviation and why (also usable between `review` and `open`, i.e. while `reviewed`). For an `unscripted` encounter, the recorded work is already done — there's nothing to execute — so this is where the agent makes any follow-up changes the review's findings called for; if the review raised nothing actionable, there's nothing further to do here.

**`open` → `completed`** — for a `scripted` encounter, once all work is finished, run the steps described in `Verification`. For an `unscripted` encounter (no `Verification` section), confirm the recorded `Requirements`/`Rationale` are still accurate and any follow-up changes from `open` are done. Either way, confirm with the user before marking it complete — do not do this unilaterally — then run `mcp__crypts-and-commits__encounter_complete(name, message)`. A message is optional.

**`draft`/`reviewed`/`open` → `abandoned`** — on request from the user, run `mcp__crypts-and-commits__encounter_abandon(name, message)` (message required). Not available once an encounter is `completed`.
