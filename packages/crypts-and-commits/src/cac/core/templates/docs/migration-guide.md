# Crypts and Commits Sourcebook Migration Guide

**Current sourcebook schema version: 1**

## Purpose

The `.sourcebook` domain model is versioned. `world.md` carries a
`schema_version` frontmatter attribute, stamped onto every sourcebook
`cac bootstrap init` creates from scratch. A sourcebook created before this
attribute existed has no such value; treat a missing attribute as version 1 -
the format that existed before versioning was introduced.

`cac bootstrap init` checks an *existing* `world.md`'s `schema_version`
against the version the installed `cac` package expects, and reports if the
sourcebook is behind (needs migration) or ahead (the installed `cac` is
older than the sourcebook and should be upgraded). Bootstrap only reports -
it never edits `world.md` itself. Migrating the content is the coding
assistant's job, guided by this document, via the `world-manager` skill.

There is deliberately no separate migration *tool*: a hand-maintained
migration engine would be complex, rarely exercised, and far less adaptable
than having the agent read this guide and make the changes itself. This
document is the source of truth an agent consults to do that.

## Maintaining this guide

Whenever `SOURCEBOOK_SCHEMA_VERSION` (`core/config.py`) is bumped, add a new
`## Migrating from version N to N+1` section below, in the same change, and
update the "Current sourcebook schema version" line above to match. Each
section should give the agent every concrete change needed to bring a
sourcebook fully onto the new version - what changed structurally, and
exactly how to apply it.

## Generic migration procedure

This procedure applies to every migration, regardless of which
version-to-version section(s) below it in this document. Follow it in
addition to, not instead of, the specific steps in each applicable section.

A real migration is very likely to need direct edits to `.sourcebook/`
files. The generic per-object setters the MCP/CLI surface exposes
(`world_set`, `lore_set_summary`, and similar) cannot perform arbitrary
structural changes a schema change may require - renaming a frontmatter key
across every file of a type, restructuring body sections, and the like. This
means a migration is the one sanctioned exception to the project's normal
`.sourcebook`-is-MCP/CLI-only guardrail, and that exception must be entered
and exited deliberately:

1. **Get explicit, informed approval before disabling any guardrail
   mechanism.** This is a bigger ask than a normal encounter approval - it
   is turning off a project safety mechanism, not just approving a plan.
   Explain to the developer which mechanism(s) will be disabled and why,
   and wait for an explicit yes.
2. **Record the current state of every guardrail mechanism in force for
   this session before touching anything**, so it can be restored exactly:
   - Claude Code: the `Edit(.sourcebook/**)` deny rule in
     `.claude/settings.json`.
   - Codex: the `PreToolUse` sourcebook-guard hook registration in
     `.codex/config.toml` (and the hook script it points to).
3. **Temporarily remove or disable the applicable guardrail mechanism(s).**
4. **Perform the migration's direct file edits**, following the
   version-specific section(s) below that apply.
5. **Restore every guardrail mechanism touched in step 3 to its exact prior
   state immediately afterward - unconditionally**, even if the migration
   is aborted or fails partway through. Do not leave the project
   unguarded because a migration didn't finish cleanly.
6. **Only after the guardrail is restored**, verify the migrated content
   through normal MCP/CLI calls (`world_get`, `lore_list`/`lore_get`,
   `region_list`/`region_get`, `campaign_list`/`campaign_get`,
   `encounter_list`/`encounter_get`, as applicable to what changed), and set
   the new version with `world_set("schema_version", "<new version>")`
   (MCP) or `cac world set schema_version <new version>` (CLI).
7. **Confirm with the developer** that the guardrail was restored and the
   migration verified, before considering the migration done.

## Version-specific migrations

There are no migrations documented yet - the sourcebook schema is at
version 1, the version this document itself introduces, and no format
change has happened since. When `SOURCEBOOK_SCHEMA_VERSION` is next bumped,
its section goes here, in this form:

```
## Migrating from version 1 to 2

<What changed structurally, and exactly how to apply it - which files,
which attributes or body sections, in what order.>
```
