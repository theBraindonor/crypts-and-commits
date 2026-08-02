---
name: world-manager
description: Manage this project's world summary, lore (standards, conventions, and best practices), and regions (documented paths within the repository) through the crypts-and-commits MCP server, falling back to the cac CLI when the server is unavailable. Use when asked to view or set the project's world summary, create/update/enable/disable a lore entry, assign lore to the world or to a region, create/update a region or its path, or to gather/prime project context before other work begins.
allowed-tools: Bash(cac *), mcp__crypts-and-commits
---

# World Manager

Owns the project's static world-building context: the world summary, lore, and regions. Work exclusively through the `crypts-and-commits` MCP server's tools when they are available for this session — never create, read, edit, move, or delete anything under `.sourcebook/` directly, whether with file tools or shell commands. Fall back to the `cac` CLI only when the MCP server is not connected for this session; the CLI covers the exact same operations (see each tool's "CLI fallback" pointer below).

If a command reports that the project hasn't been bootstrapped (no world file), stop and ask the developer to run `cac bootstrap init` themselves. Never run `cac bootstrap init` on their behalf, under any circumstance — this applies regardless of whether you'd otherwise reach for the MCP server or the CLI, since `bootstrap` is intentionally not exposed over MCP at all.

## World

The world is a single file summarizing the project's goals and purpose. It's the first thing to read when building context for other work.

- `mcp__crypts-and-commits__world_get()` — show the current summary and its frontmatter attributes. CLI fallback: `cac world get --help`.
- `mcp__crypts-and-commits__world_set(key, value)` — set a frontmatter attribute. CLI fallback: `cac world set --help`.
- `mcp__crypts-and-commits__world_set_body(body)` — replace the summary text. CLI fallback: `cac world set-body --help`.

## Lore

A lore entry captures a standard, convention, or best practice to apply when reviewing an encounter's plan. Lore assigned to the world is global and applies to every encounter. Lore assigned to a region only applies to encounters that take place in that region. A lore entry can be assigned to more than one region.

- `mcp__crypts-and-commits__lore_list(cursor)` — list all lore entries by name, paged under the response budget. CLI fallback: `cac lore list --help`.
- `mcp__crypts-and-commits__lore_get(name)` — show a lore entry's frontmatter (`enabled`, `assigned_to_world`, `assigned_regions`, `summary`) and body. CLI fallback: `cac lore get --help`.
- `mcp__crypts-and-commits__lore_create(name, body, summary)` — create a new entry. `summary` (max 500 characters) is required alongside `body`: draft it from the body you just wrote and have the developer approve or edit it before the call, so the summary never drifts from the text it stands in for. CLI fallback: `cac lore create --help`.
- `mcp__crypts-and-commits__lore_update(name, body, summary)` — replace an entry's body. `summary` is required for the same reason. CLI fallback: `cac lore update --help`.
- `mcp__crypts-and-commits__lore_set_summary(name, summary)` — set the routing summary shown by `prime` calls (max 500 characters) without touching the body. CLI fallback: `cac lore set-summary --help`.
- `mcp__crypts-and-commits__lore_delete(name)` — remove an entry, unconditionally. CLI fallback: `cac lore delete --help` (the CLI additionally supports a `--yes`/`-y` confirmation skip; the MCP tool always deletes without prompting).
- `mcp__crypts-and-commits__lore_enable(name)` / `mcp__crypts-and-commits__lore_disable(name)` — toggle whether an entry is currently in force. Skip disabled lore when reviewing encounters. CLI fallback: `cac lore enable --help` / `cac lore disable --help`.
- `mcp__crypts-and-commits__lore_assign_world(name)` / `mcp__crypts-and-commits__lore_unassign_world(name)` — make an entry global. CLI fallback: `cac lore assign-world --help` / `cac lore unassign-world --help`.
- `mcp__crypts-and-commits__lore_assign_region(name, region)` / `mcp__crypts-and-commits__lore_unassign_region(name, region)` — scope an entry to a region. CLI fallback: `cac lore assign-region --help` / `cac lore unassign-region --help`.

## Regions

A region documents a path within the repository that needs its own conventions, tech stack, or tooling described — e.g. a "frontend" and a "backend" region in a web app.

- `mcp__crypts-and-commits__region_list(cursor)` — list all regions by name, paged under the response budget. CLI fallback: `cac region list --help`.
- `mcp__crypts-and-commits__region_get(name)` — show a region's frontmatter (`path`, `assigned_lore`, `summary`) and body. CLI fallback: `cac region get --help`.
- `mcp__crypts-and-commits__region_create(name, body, summary, path)` — create a new region. `summary` (max 500 characters) is required alongside `body`, same generate-and-approve rule as lore. `path` isn't validated against the filesystem — regions may be aspirational. CLI fallback: `cac region create --help`.
- `mcp__crypts-and-commits__region_update(name, body, summary)` — replace a region's body. `summary` is required for the same reason. CLI fallback: `cac region update --help`.
- `mcp__crypts-and-commits__region_set_summary(name, summary)` — set the routing summary shown by `prime` calls without touching the body. CLI fallback: `cac region set-summary --help`.
- `mcp__crypts-and-commits__region_set_path(name, path)` — set or change the path a region covers. CLI fallback: `cac region set-path --help`.
- `mcp__crypts-and-commits__region_delete(name)` — remove a region, unconditionally. CLI fallback: `cac region delete --help` (the CLI additionally supports a `--yes`/`-y` confirmation skip; the MCP tool always deletes without prompting).

## Prime

`prime` assembles cross-object context server-side, in one call, instead of chaining individual world/lore/region reads by hand:

- `mcp__crypts-and-commits__prime_get()` — the global prime bundle: world (full — frontmatter + body) + world-assigned enabled lore (`name` + `summary` only) + region map (per region: `summary` + `path` + assigned-lore *names*, not their summaries or bodies) + the active campaign's full body (not its encounter list — that stays a separate, on-demand `mcp__crypts-and-commits__encounter_list` call). CLI fallback: `cac prime get --help`.
- `mcp__crypts-and-commits__prime_applicable_lore(encounter, campaign, cursor)` — the exact enabled lore set that applies to a specific encounter (world-assigned lore ∪ lore assigned to that encounter's region(s)), as `name` + `summary` + `ref` entries. `ref` is the lore name — hydrate it with `mcp__crypts-and-commits__lore_get(ref)` when you need the exact rule text, not just its summary. Paged under the response budget; pass the cursor from a truncated page's notice to continue. CLI fallback: `cac prime applicable-lore --help`.

Both calls return **summaries**, never lore bodies — summaries are a routing signal (what exists, roughly), not a substitute for the governing text. When a lore entry has no summary yet, the field carries an explicit placeholder saying so; treat that as a prompt to read the body directly rather than assuming there's nothing to know.

## Docs

Docs are read-only, framework-owned reference guides packaged with `cac` itself — not `.sourcebook` content, and not user-editable. They exist so deep procedural or structural detail can be pulled into context on demand instead of being carried in every project's `CLAUDE.md`/`AGENTS.md`.

- `mcp__crypts-and-commits__docs_list(cursor)` — list registered docs by `name` + `summary`, paged under the response budget. CLI fallback: `cac docs list --help`.
- `mcp__crypts-and-commits__docs_get(name)` — show a doc's full body, e.g. `docs_get("workflow")` for the Workflow Reference Guide (the `.sourcebook` domain model's structure, status lifecycles, and workflow procedure in full). CLI fallback: `cac docs get --help`.

## Sourcebook schema version

`world.md` carries a `schema_version` frontmatter attribute — present on every sourcebook `cac bootstrap init` creates; a sourcebook bootstrapped before this attribute existed has none, which means version 1. `cac bootstrap init` reports when an existing sourcebook is behind or ahead of what the installed `cac` expects, but never migrates it itself — that's this skill's job, on request.

When asked to check for or perform a sourcebook migration/upgrade:

1. Read the world's `schema_version` (from `mcp__crypts-and-commits__world_get()` or `mcp__crypts-and-commits__prime_get()`; absent means 1) and compare it against the current version stated at the top of `mcp__crypts-and-commits__docs_get("migration-guide")`. CLI fallback: `cac world get --help` / `cac docs get migration-guide`.
2. If it's already current, say so and stop.
3. If it's behind, relay the guide's generic guardrail-suspend/restore procedure and its applicable version-specific section(s) to the developer, and get their explicit approval before disabling any guardrail mechanism — this is a bigger ask than a normal approval, since it means temporarily turning off the project's `.sourcebook`-is-MCP/CLI-only guardrail.
4. Apply the guide's steps exactly, restoring every guardrail mechanism you disabled before considering the work done, then set the new version with `mcp__crypts-and-commits__world_set(key="schema_version", value="<new version>")`. CLI fallback: `cac world set --help`.
5. Confirm with the developer that the guardrail was restored and the migration verified.

Never assume a sourcebook is out of date, and never start suspending a guardrail, without reading the guide's stated current version and getting the developer's approval first.

## Priming context: the disclosure ladder

The **procedure** below for going deeper is authored once, here in the skill — it does not live in any tool payload. Tool calls return only the data traversed on (bundles, summaries, edge names); re-sending this traversal prose on every call would be the per-call token churn the ladder exists to avoid. Four steps, each going one tier deeper only when the task actually needs it:

1. **Orient** — `mcp__crypts-and-commits__prime_get()`, once at the start of a session or before other work (this is also `campaign-manager`'s first step, since the bundle already includes the active campaign body). Gives world full + world-lore summaries + region map + campaign body in one round trip. Summarize what you found rather than dumping raw tool output.
2. **Focus a task** — once a specific region is in scope (e.g. the region(s) an encounter is assigned to), `mcp__crypts-and-commits__region_get(region)` for its full body and its `assigned_lore` names, then `mcp__crypts-and-commits__lore_get(name)` per assigned name to read that lore's `summary` (not yet its body) — enough to judge which of that region's lore looks relevant before going further.
3. **Review a plan** — the only step that needs exact, ground-truth text. Run `mcp__crypts-and-commits__prime_applicable_lore(encounter)` to resolve the finite applicable set (world-assigned ∪ the encounter's region-assigned enabled lore) as summaries, then hydrate each one with `mcp__crypts-and-commits__lore_get(ref)` and check the plan against the full body — never the summary. Summaries route which lore is in scope; only the body is authoritative for a compliance verdict. This is the step the reviewer subagent in `campaign-manager`'s draft → reviewed gate performs.
4. **Go deeper** — when a task needs full procedural or structural detail beyond what any summary above covers (e.g. the exact status-transition rules or cross-type connections behind this skill), `mcp__crypts-and-commits__docs_list()` to see what's registered, then `mcp__crypts-and-commits__docs_get(name)` to pull one in whole. Most sessions never need this step — reach for it only when the ladder above genuinely isn't enough.
