---
name: world-manager
description: Manage this project's world summary, lore (standards, conventions, and best practices), and regions (documented paths within the repository) through the cac CLI. Use when asked to view or set the project's world summary, create/update/enable/disable a lore entry, assign lore to the world or to a region, create/update a region or its path, or to gather/prime project context before other work begins.
allowed-tools: Bash(cac *)
---

# World Manager

Owns the project's static world-building context: the world summary, lore, and regions. Work exclusively through the `cac` CLI — never create, read, edit, move, or delete anything under `.sourcebook/` directly, whether with file tools or shell commands.

If a command reports that the project hasn't been bootstrapped (no world file), stop and ask the developer to run `cac bootstrap init` themselves. Never run `cac bootstrap init` on their behalf, under any circumstance.

## World

The world is a single file summarizing the project's goals and purpose. It's the first thing to read when building context for other work.

- `cac world get` — show the current summary and its frontmatter attributes.
- `cac world set <key> <value>` — set a frontmatter attribute.
- `cac world set-body [--body "..."]` — replace the summary text.

## Lore

A lore entry captures a standard, convention, or best practice to apply when reviewing an encounter's plan. Lore assigned to the world is global and applies to every encounter. Lore assigned to a region only applies to encounters that take place in that region. A lore entry can be assigned to more than one region.

- `cac lore list` — list all lore entries by name.
- `cac lore get <name>` — show a lore entry's frontmatter (`enabled`, `assigned_to_world`, `assigned_regions`, `summary`) and body.
- `cac lore create <name> --body "..." --summary "..."` — create a new entry. `--summary` (max 500 characters) is required alongside `--body`: draft it from the body you just wrote and have the developer approve or edit it before the call, so the summary never drifts from the text it stands in for.
- `cac lore update <name> --body "..." --summary "..."` — replace an entry's body. `--summary` is required for the same reason.
- `cac lore set-summary <name> <summary>` — set the routing summary shown by `cac prime` calls (max 500 characters) without touching the body.
- `cac lore delete <name>` — remove an entry.
- `cac lore enable <name>` / `cac lore disable <name>` — toggle whether an entry is currently in force. Skip disabled lore when reviewing encounters.
- `cac lore assign-world <name>` / `cac lore unassign-world <name>` — make an entry global.
- `cac lore assign-region <name> <region>` / `cac lore unassign-region <name> <region>` — scope an entry to a region.

## Regions

A region documents a path within the repository that needs its own conventions, tech stack, or tooling described — e.g. a "frontend" and a "backend" region in a web app.

- `cac region list` — list all regions by name.
- `cac region get <name>` — show a region's frontmatter (`path`, `assigned_lore`, `summary`) and body.
- `cac region create <name> --body "..." --summary "..." [--path <path>]` — create a new region. `--summary` (max 500 characters) is required alongside `--body`, same generate-and-approve rule as lore. `--path` isn't validated against the filesystem — regions may be aspirational.
- `cac region update <name> --body "..." --summary "..."` — replace a region's body. `--summary` is required for the same reason.
- `cac region set-summary <name> <summary>` — set the routing summary shown by `cac prime` calls without touching the body.
- `cac region set-path <name> <path>` — set or change the path a region covers.
- `cac region delete <name>` — remove a region.

## Prime

`prime` assembles cross-object context server-side, in one call, instead of chaining individual world/lore/region reads by hand:

- `cac prime get` — the global prime bundle: world (full — frontmatter + body) + world-assigned enabled lore (`name` + `summary` only) + region map (per region: `summary` + `path` + assigned-lore *names*, not their summaries or bodies) + the active campaign's full body (not its encounter list — that stays a separate, on-demand `cac encounter list` call).
- `cac prime applicable-lore <encounter> [--campaign <campaign>] [--cursor <cursor>]` — the exact enabled lore set that applies to a specific encounter (world-assigned lore ∪ lore assigned to that encounter's region(s)), as `name` + `summary` + `ref` entries. `ref` is the lore name — hydrate it with `cac lore get <ref>` when you need the exact rule text, not just its summary. Paged under the response budget; pass the cursor from a truncated page's notice to continue.

Both calls return **summaries**, never lore bodies — summaries are a routing signal (what exists, roughly), not a substitute for the governing text. When a lore entry has no summary yet, the field carries an explicit placeholder saying so; treat that as a prompt to read the body directly rather than assuming there's nothing to know.

## Priming context: the disclosure ladder

The **procedure** below for going deeper is authored once, here in the skill — it does not live in any tool payload. Tool calls return only the data traversed on (bundles, summaries, edge names); re-sending this traversal prose on every call would be the per-call token churn the ladder exists to avoid. Three steps, each going one tier deeper only when the task actually needs it:

1. **Orient** — `cac prime get`, once at the start of a session or before other work (this is also `campaign-manager`'s first step, since the bundle already includes the active campaign body). Gives world full + world-lore summaries + region map + campaign body in one round trip. Summarize what you found rather than dumping raw command output.
2. **Focus a task** — once a specific region is in scope (e.g. the region(s) an encounter is assigned to), `cac region get <region>` for its full body and its `assigned_lore` names, then `cac lore get <name>` per assigned name to read that lore's `summary` (not yet its body) — enough to judge which of that region's lore looks relevant before going further.
3. **Review a plan** — the only step that needs exact, ground-truth text. Run `cac prime applicable-lore <encounter>` to resolve the finite applicable set (world-assigned ∪ the encounter's region-assigned enabled lore) as summaries, then hydrate each one with `cac lore get <ref>` and check the plan against the full body — never the summary. Summaries route which lore is in scope; only the body is authoritative for a compliance verdict. This is the step the reviewer subagent in `campaign-manager`'s draft → reviewed gate performs.
