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
- `cac lore get <name>` — show a lore entry's frontmatter (`enabled`, `assigned_to_world`, `assigned_regions`) and body.
- `cac lore create <name> [--body "..."]` — create a new entry.
- `cac lore update <name> [--body "..."]` — replace an entry's body.
- `cac lore delete <name>` — remove an entry.
- `cac lore enable <name>` / `cac lore disable <name>` — toggle whether an entry is currently in force. Skip disabled lore when reviewing encounters.
- `cac lore assign-world <name>` / `cac lore unassign-world <name>` — make an entry global.
- `cac lore assign-region <name> <region>` / `cac lore unassign-region <name> <region>` — scope an entry to a region.

## Regions

A region documents a path within the repository that needs its own conventions, tech stack, or tooling described — e.g. a "frontend" and a "backend" region in a web app.

- `cac region list` — list all regions by name.
- `cac region get <name>` — show a region's frontmatter (`path`) and body.
- `cac region create <name> [--path <path>] [--body "..."]` — create a new region. `--path` isn't validated against the filesystem — regions may be aspirational.
- `cac region update <name> [--body "..."]` — replace a region's body.
- `cac region set-path <name> <path>` — set or change the path a region covers.
- `cac region delete <name>` — remove a region.

## Priming context

When asked to gather or prime project context (at the start of a session, or on request from `campaign-manager` before it opens an encounter):

1. `cac world get` for the project summary.
2. `cac lore list`, then `cac lore get <name>` for each entry, to find which are `enabled` and either `assigned_to_world` or assigned to a region in scope.
3. If a specific region is in scope, `cac region get <name>` for its own documented conventions.
4. Summarize what you found rather than dumping raw command output.
