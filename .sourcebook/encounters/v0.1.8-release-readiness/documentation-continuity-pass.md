---
archived: false
campaign: v0.1.8-release-readiness
created_by: John Hoff
created_on: '2026-08-05T02:55:56Z'
depends_on: []
name: documentation-continuity-pass
regions:
- crypts-and-commits
status: draft
updated_by: John Hoff
updated_on: '2026-08-05T02:55:58Z'
---

# Encounter

## Requirements

- From the top-level `README.md`, establish a clear, discoverable link into: `docs/QUICKSTART.md`; each package's own `README.md` (`packages/crypts-and-commits/README.md`, `packages/demo-api/README.md`, and `packages/demo-ui/README.md` once that package exists); and the documentation baked into the MCP server itself (currently the `workflow` and `migration-guide` docs, retrievable via `docs_list`/`docs_get`, sourced from `packages/crypts-and-commits/src/cac/core/templates/docs/`).
- Create a release history file in the root `docs/` folder (e.g. `docs/CHANGELOG.md` or `docs/RELEASE_HISTORY.md` - naming TBD when picked up) to record this and future releases. It will necessarily be light for now, covering only the first planned release.
- Decide, rather than assume, whether the existing internal design docs (`docs/context-management-design.md`, `docs/encounter-search-design.md`) belong in this navigation pass or should stay intentionally unlinked as internal/deferred design notes.
- This is a continuity/navigation pass over documentation that already exists (plus the new release history file) - not a mandate to author further net-new content beyond that.

## Rationale

The project's documentation currently exists as several disconnected pieces - the root README, per-package READMEs, `docs/QUICKSTART.md`, and the MCP-server-only `workflow`/`migration-guide` docs - with no single path from the root README that lets a new user or contributor discover all of them. That matters more once the package is publicly released, since the root README and package README become most readers' actual entry point.

A release history file, even minimal for this first release, gives that record a place to start rather than being reconstructed retroactively after later releases.

## Plan

Plan has not been described yet.

## Verification

Verification has not been described yet.
