---
name: campaign-manager
description: Manage this project's active work-tracking loop - campaigns (long-running initiatives, like a Jira Epic) and encounters (concrete units of work with Requirements/Rationale/Plan/Verification sections) - through the cac CLI. Use when asked to start a new initiative, move a campaign through its draft/open/paused/completed/abandoned lifecycle, plan a new unit of work, move an encounter through its draft/reviewed/open/completed/abandoned lifecycle, or assign an encounter to one or more regions.
allowed-tools: Bash(cac *)
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

- `cac encounter list <campaign>` — list encounter names within a campaign.
- `cac encounter get <campaign> <name>` — show an encounter's frontmatter (`status`, `regions`) and body.
- `cac encounter create <campaign> <name> [--body "..."]` — create a new encounter. The campaign must already exist.
- `cac encounter update <campaign> <name> [--body "..."]` — replace an encounter's body. Only works while status is `draft`.
- `cac encounter review <campaign> <name> --message "..."` — move `draft` → `reviewed` after a lore review. Message is required and permanently locks the content.
- `cac encounter open <campaign> <name> [--message "..."]` — move `reviewed` → `open` and begin execution. Message is optional.
- `cac encounter record-message <campaign> <name> --message "..."` — append a note without changing status. Works while `reviewed` or `open`.
- `cac encounter complete <campaign> <name> [--message "..."]` — move `open` → `completed` once verification passes. Message is optional.
- `cac encounter abandon <campaign> <name> --message "..."` — move `draft`, `reviewed`, or `open` → `abandoned`. Not available once `completed`. Message is required.
- `cac encounter assign-region <campaign> <name> <region>` / `cac encounter unassign-region <campaign> <name> <region>` — an encounter may be assigned to one or more regions. This link is recorded only on the encounter.
- `cac encounter delete <campaign> <name>` — remove an encounter.

## Encounter Lifecycle

**`draft`** — the encounter is being documented and planned. Write the `Requirements`, `Rationale`, and `Plan` sections; leave `Verification` describing how the work will be checked once it's done. This is the only status in which `cac encounter update` can replace the body.

**`draft` → `reviewed`** — before reviewing, gather applicable lore (ask `world-manager`, or gather it directly): all `enabled` lore that is `assigned_to_world`, plus all `enabled` lore assigned to any region the encounter is assigned to. Check the Plan against each item. Confirm with the user before running `cac encounter review <campaign> <name> --message "<review summary>"` — this permanently locks the Requirements, Rationale, Plan, and Verification sections; they can no longer be replaced with `update`, only appended to.

**`reviewed` → `open`** — get explicit approval from the user, then run `cac encounter open <campaign> <name> [--message "<any extra instructions/feedback>"]`. A message is optional here.

**`open`** — execute the Plan. If the Plan or Verification needs to change based on what's found during implementation, do not attempt to edit them directly — use `cac encounter record-message <campaign> <name> --message "..."` to record the deviation and why (also usable between `review` and `open`, i.e. while `reviewed`).

**`open` → `completed`** — once all work is finished, run the steps described in Verification. Once verification passes, confirm with the user before marking it complete — do not do this unilaterally — then run `cac encounter complete <campaign> <name> [--message "<closing notes>"]`. A message is optional.

**`draft`/`reviewed`/`open` → `abandoned`** — on request from the user, run `cac encounter abandon <campaign> <name> --message "<reason>"` (message required). Not available once an encounter is `completed`.
