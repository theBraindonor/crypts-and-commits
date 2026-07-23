---
name: campaign-manager
description: Manage this project's active work-tracking loop - campaigns (long-running initiatives, like a Jira Epic) and encounters (concrete units of work with Requirements/Rationale/Plan/Verification sections) - through the cac CLI. Use when asked to start a new initiative, plan a new unit of work, move an encounter through its draft/open/completed/abandoned lifecycle, or assign an encounter to one or more regions.
allowed-tools: Bash(cac *)
---

# Campaign Manager

Owns the project's active work-tracking loop: campaigns and the encounters within them. Work exclusively through the `cac` CLI — never create, read, edit, move, or delete anything under `.sourcebook/` directly, whether with file tools or shell commands.

If a command reports that the project hasn't been bootstrapped, stop and ask the developer to run `cac bootstrap init` themselves. Never run it on their behalf.

## Campaigns

A campaign is a long-running initiative, similar to an "Epic" in Jira-style work tracking (e.g. "Create the MVP", "Add Payment Processing", a version increment). It's expected to require many encounters, completed over time, before it's done.

- `cac campaign list` — list all campaigns by name.
- `cac campaign get <name>` — show a campaign's frontmatter (`status`) and body.
- `cac campaign create <name> [--body "..."]` — create a new campaign.
- `cac campaign update <name> [--body "..."]` — replace a campaign's body.
- `cac campaign set-status <name> <status>` — `draft`, `open`, `completed`, or `abandoned`.
- `cac campaign delete <name>` — remove a campaign.

## Encounters

An encounter is a concrete unit of work within a campaign: a plan the agent is expected to execute, with `Requirements`, `Rationale`, `Plan`, and `Verification` sections in its body.

- `cac encounter list <campaign>` — list encounter names within a campaign.
- `cac encounter get <campaign> <name>` — show an encounter's frontmatter (`status`, `regions`) and body.
- `cac encounter create <campaign> <name> [--body "..."]` — create a new encounter. The campaign must already exist.
- `cac encounter update <campaign> <name> [--body "..."]` — replace an encounter's body.
- `cac encounter set-status <campaign> <name> <status>` — `draft`, `open`, `completed`, or `abandoned`.
- `cac encounter assign-region <campaign> <name> <region>` / `cac encounter unassign-region <campaign> <name> <region>` — an encounter may be assigned to one or more regions. This link is recorded only on the encounter.
- `cac encounter delete <campaign> <name>` — remove an encounter.

## Lifecycle

**`draft`** — the encounter is being documented and planned. Write the `Requirements`, `Rationale`, and `Plan` sections; leave `Verification` describing how the work will be checked once it's done.

**`draft` → `open`** — before opening, review applicable lore (ask `world-manager`, or gather it directly): all `enabled` lore that is `assigned_to_world`, plus all `enabled` lore assigned to any region the encounter is assigned to. Check the Plan against each item. Then get explicit approval from the user — do not open an encounter without it — and run `cac encounter set-status <campaign> <name> open`.

**`open`** — execute the Plan.

**`open` → `completed`** — once all work is finished, run the steps described in Verification. Once verification passes, confirm with the user before marking it complete — do not do this unilaterally — then run `cac encounter set-status <campaign> <name> completed`.

**`abandoned`** — available at any point, on request from the user, with no gate: `cac encounter set-status <campaign> <name> abandoned`.
