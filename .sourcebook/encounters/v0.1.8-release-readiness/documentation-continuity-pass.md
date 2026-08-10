---
archived: false
campaign: v0.1.8-release-readiness
created_by: John Hoff
created_on: '2026-08-05T02:55:56Z'
depends_on: []
name: documentation-continuity-pass
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-08-10T06:27:36Z'
---

# Encounter

## Requirements

- Rewrite the root `README.md` as the project's formal front door, structured as five parts in order: (1) a hero banner (`docs/images/banner-xlarge.png`) plus a brief intro to CAC and its purpose; (2) discoverable links to `docs/QUICKSTART.md` and the packaged `workflow`/`migration-guide` docs; (3) an introduction to the sourcebook domain model's objects and personas - World, Region, Lore, Campaign, Encounter, AI Assistant, and User/Game Master; (4) an explanation of this repository's own layout and how it's organized to both bootstrap `cac`'s own development and host the `demo-api`/`demo-ui` demonstration application; (5) full instructions to build and run the demo apps and to explore this repository's own `.sourcebook`.
- Link from the README to: `docs/QUICKSTART.md`, `packages/crypts-and-commits/src/cac/core/templates/docs/workflow.md`, `packages/crypts-and-commits/src/cac/core/templates/docs/migration-guide.md`, and each package's own README (`packages/crypts-and-commits/README.md`, `packages/demo-api/README.md`, `packages/demo-ui/README.md`).
- Create `docs/CHANGELOG.md` (Keep a Changelog style), with an "Unreleased" entry describing the state being prepared for the first release, and link it from the README. This is a new, minimal file - not a mandate to author further net-new content beyond it.
- Leave `docs/context-management-design.md` and `docs/encounter-search-design.md` unlinked from the README - confirmed with the developer as internal/deferred design notes, out of scope for this pass.
- This is primarily a continuity/navigation and structural pass over documentation that already exists, plus the one new changelog file.

## Rationale

The project's documentation currently exists as several disconnected pieces - the root README, per-package READMEs, `docs/QUICKSTART.md`, and the MCP-server-only `workflow`/`migration-guide` docs - with no single path from the root README that lets a new user or contributor discover all of them. That matters more once the package is publicly released, since the root README becomes most readers' actual entry point. A dedicated domain-model/personas section also gives a first-time reader the tabletop metaphor's vocabulary (World, Region, Lore, Campaign, Encounter, Assistant, Game Master) before they hit it in the Quickstart or in an agent session, rather than assuming it's already familiar. A release history file, even minimal for this first release, gives that record a place to start rather than being reconstructed retroactively after later releases.

## Plan

1. Embed the hero banner (`docs/images/banner-xlarge.png`) at the top of `README.md`, sized so it doesn't dominate a GitHub-rendered page, followed by a brief intro paragraph restating CAC's purpose and the GM/assistant metaphor (consistent with `world.md`'s body, not copy-pasted verbatim).
2. Add a "Documentation" section linking `docs/QUICKSTART.md`, the `workflow` doc, the `migration-guide` doc, and the new `docs/CHANGELOG.md`.
3. Add a "Domain Model & Personas" section briefly introducing World, Lore, Region, Campaign, and Encounter, plus the two personas - AI Assistant and User/Game Master - consistent with `world.md`'s existing "Domain model" summary and the `workflow` doc, without duplicating full procedural detail (link out to `workflow.md` for that).
4. Add a "Repository Layout" section describing the PDM workspace and its three packages (`crypts-and-commits`, `demo-api`, `demo-ui`), noting this repo dogfoods its own `.sourcebook` to drive `cac`'s own development while also hosting the demo Q&A application as a secondary, non-`cac` codebase; link to each package's README.
5. Add/refresh a "Running the demo apps" section with build/run steps for `demo-api` and `demo-ui`, verified against the current state of both packages (the existing README already has a version of this - confirm it's still accurate rather than assuming so).
6. Add an "Exploring this repository's sourcebook" section showing how to inspect this repo's own live `.sourcebook` (e.g. `cac world get`, `cac campaign list`, `cac docs get workflow`, or the MCP-server equivalents) as a concrete example of CAC dogfooding itself.
7. Create `docs/CHANGELOG.md` with a Keep a Changelog-style "Unreleased" heading summarizing what's being prepared for the first release.
8. Cross-check every link in the new README (relative paths for in-repo files) resolves correctly as rendered on GitHub.

## Verification

- Every link in the rewritten `README.md` and the new `docs/CHANGELOG.md` resolves correctly (relative paths correct; spot-checked by rendering).
- `pdm run pytest -q` and `pdm run ruff check .` / `pdm run ruff format .` stay clean per the world-assigned `clean-tests-and-lint` lore (no application code is touched by this encounter, but this confirms no incidental breakage).
- The `demo-api` and `demo-ui` build/run instructions in the README are manually re-run and confirmed to still work as written.
- Developer reviews and confirms the README covers all five required sections and reads well before the encounter is marked complete.

## Log

### Review - 2026-08-09T16:28:01Z - John Hoff

Reviewed against all five applicable lore items: clean-tests-and-lint is explicitly honored via the Verification section's pytest/ruff gate; cli-mcp-parity, console-best-practices, skills-authored-only-in-templates, and workflow-doc-source-of-truth are all correctly not implicated, since this Plan is a documentation/navigation pass only (README rewrite plus one new CHANGELOG file) that touches no cli/, mcp/, core/, or skill-template code and only links to workflow.md rather than changing what it documents. No lore conflicts found. Note for the developer's awareness (not a defect): the encounter's single region assignment (crypts-and-commits) pulls in region lore that ends up largely inert here since most of the actual work is at the repo root, outside that region's documented path - worth a quick sanity check on region scoping, but not blocking.

### Message - 2026-08-09T16:36:48Z - John Hoff

Scope deviation, approved by the developer: folding in PyPI-publish-readiness work beyond the original Plan - bumping package/workspace version to 0.2.0, dropping the git-URL install instructions in docs/QUICKSTART.md (and any other docs still referencing it) in favor of `pip install crypts-and-commits`, and finalizing docs/CHANGELOG.md's Unreleased entry as the dated [0.2.0] release - so the repository is fully ready at the moment the package is actually published to PyPI and the repo opened to the public.

### Message - 2026-08-10T04:55:47Z - John Hoff

Scope deviation, approved by the developer: rewriting packages/demo-api/README.md and packages/demo-ui/README.md themselves - each covering the package's purpose and instructions to run it, replacing most existing content (demo-api's current README is a one-line placeholder; demo-ui's is still the default Vite template README). The original Plan only scoped these two files as link targets from the root README, not as content to author/replace.

### Completed - 2026-08-10T06:27:36Z - John Hoff

Verified complete: root README.md rewritten (banner/intro, developer's own "Why Crypts and Commits" section, Documentation links, Domain Model & Personas with metaphor rationale, Repository Layout, Running the demo apps, Exploring this repository's sourcebook); docs/CHANGELOG.md created and finalized as the dated [0.2.0] release; demo-api and demo-ui READMEs rewritten with purpose and run instructions. Folded-in deviations (recorded above) covered PyPI-publish readiness (version bump to 0.2.0 across pyproject.toml/pdm.lock, git-URL install instructions dropped from QUICKSTART.md) and the two package README rewrites. All links verified resolving, pytest (810 passed) and ruff clean throughout, demo-api/demo-ui build/run/test instructions manually re-run and confirmed working. Developer reviewed and approved completion.
