---
name: campaign-manager
description: Manage this project's active work-tracking loop - campaigns (long-running initiatives, like a Jira Epic) and encounters (concrete units of work with Requirements/Rationale/Plan/Verification sections) - through the cac CLI. Use when asked to start a new initiative, move a campaign through its draft/open/paused/completed/abandoned lifecycle, plan a new unit of work, move an encounter through its draft/reviewed/open/completed/abandoned lifecycle, or assign an encounter to one or more regions.
allowed-tools: Bash(cac *), Task
---

# Campaign Manager

Owns the project's active work-tracking loop: campaigns and the encounters within them. Work exclusively through the `cac` CLI — never create, read, edit, move, or delete anything under `.sourcebook/` directly, whether with file tools or shell commands.

If a command reports that the project hasn't been bootstrapped, stop and ask the developer to run `cac bootstrap init` themselves. Never run it on their behalf.

## Campaigns

A campaign is a long-running initiative, similar to an "Epic" in Jira-style work tracking (e.g. "Create the MVP", "Add Payment Processing", a version increment). It's expected to require many encounters, completed over time, before it's done.

- `cac campaign list` — list all campaigns by name, with their current status.
- `cac campaign get <name>` — show a campaign's frontmatter (`status`, `created_on`/`created_by`/`updated_on`/`updated_by`) and body.
- `cac campaign create <name> [--body "..."]` — create a new campaign, in `draft` status.
- `cac campaign update <name> [--body "..."]` — replace a campaign's body.
- `cac campaign open <name>` — move `draft` or `paused` → `open` and begin work. Only one campaign may be `open` at a time.
- `cac campaign pause <name>` — move `open` → `paused`. Fails if the campaign has an encounter that is currently `open`.
- `cac campaign complete <name>` — move `open` or `paused` → `completed`. Fails if the campaign has an encounter that is currently `open`.
- `cac campaign abandon <name>` — move `draft`, `open`, or `paused` → `abandoned`. Not available once `completed`. Fails if the campaign has an encounter that is currently `open`.
- `cac campaign delete <name>` — remove a campaign.

## Campaign Lifecycle

**`draft`** — the campaign was just created and hasn't started yet.

**`draft`/`paused` → `open`** — run `cac campaign open <name>`. Only one campaign may be `open` at a time; if another campaign is already `open`, this fails naming that campaign — pause or complete it first.

**`open` → `paused`** — run `cac campaign pause <name>` to set work aside without completing it. Fails, naming the offending encounter(s), if any encounter under the campaign is currently `open`; complete or abandon those encounters first (or wait for them to finish).

**`open`/`paused` → `completed`** — run `cac campaign complete <name>` once the initiative is done. Same open-encounter restriction as `pause`.

**`draft`/`open`/`paused` → `abandoned`** — run `cac campaign abandon <name>`. Not available once `completed`. Same open-encounter restriction as `pause`.

## Encounters

An encounter is a concrete unit of work within a campaign: a plan the agent is expected to execute, with `Requirements`, `Rationale`, `Plan`, and `Verification` sections in its body.

### Choosing the campaign

The campaign is **optional** on every encounter command: when omitted, it defaults to the currently **active** (the single `open`) campaign. Since normal work happens inside the open campaign, you usually don't pass a campaign at all. Pass `--campaign <campaign>` (`-c`) only to act on a *different* campaign.

- If no campaign is open and you don't pass `--campaign`, the command fails asking you to open a campaign or pass one explicitly.
- The **mutating** commands (`create`, `update`, `delete`, `review`, `open`, `record-message`, `complete`, `abandon`, `assign-region`, `unassign-region`) refuse a `--campaign` that is `completed` or `abandoned` — you cannot change encounters in a closed campaign.
- The **read** commands (`get`, `list`) accept any existing campaign, including `completed`/`abandoned` ones, so past work stays inspectable.

In the command forms below, `[--campaign <campaign>]` is shown explicitly, but omit it to use the active campaign.

- `cac encounter list [--campaign <campaign>]` — list encounter names within a campaign, ordered oldest-updated first (ascending by `updated_on`).
- `cac encounter get <name> [--campaign <campaign>]` — show an encounter's frontmatter (`status`, `regions`) and body.
- `cac encounter create <name> [--campaign <campaign>] [--body "..."]` — create a new encounter. The campaign must already exist and not be completed/abandoned.
- `cac encounter update <name> [--campaign <campaign>] [--body "..."]` — replace an encounter's body. Only works while status is `draft`.
- `cac encounter review <name> [--campaign <campaign>] --message "..."` — move `draft` → `reviewed` after a lore review. Message is required and permanently locks the content.
- `cac encounter open <name> [--campaign <campaign>] [--message "..."]` — move `reviewed` → `open` and begin execution. Message is optional.
- `cac encounter record-message <name> [--campaign <campaign>] --message "..."` — append a note without changing status. Works while `reviewed` or `open`.
- `cac encounter complete <name> [--campaign <campaign>] [--message "..."]` — move `open` → `completed` once verification passes. Message is optional.
- `cac encounter abandon <name> [--campaign <campaign>] --message "..."` — move `draft`, `reviewed`, or `open` → `abandoned`. Not available once `completed`. Message is required.
- `cac encounter assign-region <name> <region> [--campaign <campaign>]` / `cac encounter unassign-region <name> <region> [--campaign <campaign>]` — an encounter may be assigned to one or more regions. This link is recorded only on the encounter.
- `cac encounter delete <name> [--campaign <campaign>]` — remove an encounter.

## Encounter Lifecycle

**`draft`** — the encounter is being documented and planned. Write the `Requirements`, `Rationale`, and `Plan` sections; leave `Verification` describing how the work will be checked once it's done. This is the only status in which `cac encounter update` can replace the body.

**`draft` → `reviewed`** — this gate is performed by an **independent, fresh reviewer subagent**, never inline by the agent that authored the plan. An agent reviewing its own plan just re-checks it against the priors that produced it — a rubber stamp — so **do not review the Plan yourself**.

1. **Spawn a fresh reviewer.** Use the `Task` tool with `subagent_type: "general-purpose"` — a fresh agent, **never a fork** (a fork inherits the authoring conversation and reproduces its bias). Hand it the [reviewer prompt template](#reviewer-subagent-prompt-template) below, filling in only the encounter and campaign names. Pass nothing else — no lore, no analysis of your own — so the review stays independent and also tests whether the encounter is self-contained enough to survive a context reset.
2. **Let it review within bounds.** The subagent primes the world/lore itself, checks the Plan against applicable lore within a bounded reading surface, and returns findings, a verdict (**PASS-WITH-NOTES** / **REJECT** / **NOT-REVIEWABLE**), and a *proposed* review message. It does **not** run any `cac encounter` command — the transition is the human's to authorize.
3. **Relay, then transition from the main thread.** Relay the reviewer's findings and verdict to the user. Only on the user's approval does the **main thread** run `cac encounter review <name> --message "<the reviewer's findings>"`; the message content is the reviewer's independent findings, not a self-summary. This permanently locks the Requirements, Rationale, Plan, and Verification sections — they can no longer be replaced with `update`, only appended to.

If the verdict is **REJECT** or **NOT-REVIEWABLE**, do not transition: relay the reviewer's reasons, revise the draft with `cac encounter update` (still allowed while `draft`), and spawn a fresh reviewer again.

#### Reviewer subagent prompt template

Spawn with `subagent_type: "general-purpose"` (fresh, not a fork). Replace `<ENCOUNTER>` and `<CAMPAIGN>`; do not add anything else to the prompt.

```
You are an independent reviewer for a Crypts and Commits (CAC) "encounter" — a
planned unit of work. Review it critically against the project's lore
(standards and conventions). You did not write this plan; do not assume it is
sound, and you are expected to reject it if it does not hold up.

Encounter: <ENCOUNTER>
Campaign:  <CAMPAIGN>

Prime the context yourself — do not accept any summary of it. Use the
`world-manager` skill if it is available, or run these reads directly:
- `cac world get` — read the world summary.
- `cac lore list`, then `cac lore get <name>` for each entry. Applicable lore is
  every `enabled` entry with `assigned_to_world: true`, PLUS every `enabled`
  entry assigned to a region this encounter is assigned to.
- `cac encounter get <ENCOUNTER> -c <CAMPAIGN>` — read the encounter and note its
  `regions`. For each region, `cac region get <region>` for its documented
  `path` and assigned lore.

Check the Plan against each applicable lore item.

Bounded reading surface — you may READ only:
- the encounter body,
- the applicable lore bodies (including any paths or globs the lore names),
- the assigned regions' documented `path`s,
- files the Plan explicitly names.
This bound is an instruction, not a technical sandbox — nothing stops you
reading elsewhere, so honor it deliberately. If you suspect a lore-relevant area
the Plan did NOT cite, FLAG it as unverifiable / possibly out of scope — do not
go read it or reverse-engineer intent from the wider repo. Catching such sins of
omission is valuable; chasing them is not.

Return this and nothing more:
1. Findings — for each applicable lore item, whether the Plan honors it, with any
   conflict or gap. List "flagged but unverified" concerns separately.
2. Verdict — exactly one of:
   - PASS-WITH-NOTES — reviewable and consistent with lore;
   - REJECT — the Plan conflicts with lore;
   - NOT-REVIEWABLE — too underspecified to review within the cited surface.
3. A proposed one-paragraph `cac encounter review --message` string capturing
   your findings.

Do NOT run `cac encounter review`, `open`, `update`, or any other mutating `cac`
command, and do not edit any files. You are reviewing only.
```

**`reviewed` → `open`** — get explicit approval from the user, then run `cac encounter open <name> [--message "<any extra instructions/feedback>"]`. A message is optional here.

**`open`** — execute the Plan. If the Plan or Verification needs to change based on what's found during implementation, do not attempt to edit them directly — use `cac encounter record-message <name> --message "..."` to record the deviation and why (also usable between `review` and `open`, i.e. while `reviewed`).

**`open` → `completed`** — once all work is finished, run the steps described in Verification. Once verification passes, confirm with the user before marking it complete — do not do this unilaterally — then run `cac encounter complete <name> [--message "<closing notes>"]`. A message is optional.

**`draft`/`reviewed`/`open` → `abandoned`** — on request from the user, run `cac encounter abandon <name> --message "<reason>"` (message required). Not available once an encounter is `completed`.
