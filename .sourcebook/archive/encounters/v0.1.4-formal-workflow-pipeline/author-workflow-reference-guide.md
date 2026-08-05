---
archived: true
campaign: v0.1.4-formal-workflow-pipeline
created_by: John Hoff
created_on: '2026-07-28T03:12:42Z'
depends_on: []
name: author-workflow-reference-guide
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-08-04T06:48:04Z'
---

## Requirements

- Add a new packaged template `docs/workflow.md` under `packages/crypts-and-commits/src/cac/core/templates/` (a new `docs` template subpackage, following the existing `templates/sourcebook/`, `templates/skills/`, `templates/codex/` pattern — including its own `__init__.py` so it's `importlib.resources`-loadable and ships inside the built wheel).
- Title the document "Crypts and Commits Workflow Reference Guide" (corrected from the campaign discussion's "Crypts and Crypts" — the project's abbreviation is CAC, never "C&C", per CLAUDE.md).
- Document every `.sourcebook` content type — world, lore, region, campaign, encounter:
  - What it represents and where it lives on disk (conceptually, without encouraging direct file access — this doc describes the domain model, not a filesystem browsing guide).
  - Its frontmatter attributes and body structure (e.g. encounter's fixed Requirements/Rationale/Plan/Verification sections).
  - Its workflow/status lifecycle where one exists (lore: enabled/disabled; campaign: draft/open/paused/completed/abandoned; encounter: draft/reviewed/open/completed/abandoned) and the valid transitions between states, including which transitions require a message/postmortem and which lock content. World and region are singletons/unstatused — note that explicitly rather than omitting them.
  - How it connects to other types: world ↔ lore (assign/unassign, global scope), region ↔ lore (assign/unassign, scoped), campaign → encounter (containment), encounter → region (assignment, recorded only on the encounter), encounter → encounter (`depends_on`, same-campaign, no cycles).
- Explicitly out of scope for this encounter: worked examples of ideal agent-user interaction flows. That is planned as a follow-on extension to this same document, not part of this pass — do not draft it now.
- The document must reflect the *current, real* MCP tool surface, CLI command surface, and skill lifecycle steps — not a re-statement of aspirational or historical behavior.

## Rationale

This is the first encounter under v0.1.4-formal-workflow-pipeline. The campaign's thesis is that a single, formal workflow document should become the source of truth that implementation-specific skills (Claude Code, Codex, and any future assistant flavor) are authored against, rather than one flavor being treated as "primary" and others forked from it by hand. Producing that document is the prerequisite for every other campaign goal (closing the region-assignment and reviewer-approval gaps, keeping Claude/Codex skills from drifting) — nothing downstream can be derived from a spec that doesn't exist yet.

Packaging it as a template (not just a repo-root `docs/` design note like `docs/encounter-search-design.md` or `docs/context-management-design.md`) keeps it distinct from historical design docs: this is meant to be a living, current-state reference, shipped as package data the same way skill templates are, not a point-in-time design record.

## Plan

1. Create `packages/crypts-and-commits/src/cac/core/templates/docs/__init__.py` and `packages/crypts-and-commits/src/cac/core/templates/docs/workflow.md`.
2. Draft the guide's structure: one section per content type (World, Lore, Region, Campaign, Encounter), each covering purpose, attributes/body shape, status lifecycle (or "no status" for World/Region), and its connections to other types. Include a short cross-cutting section summarizing how the five types relate to each other as a whole (e.g. a simple diagram or table of the connection edges).
3. Source the lifecycle and connection details from the authoritative current implementation, not from memory of past conversations: `core/campaign.py`, `core/encounter.py`, `core/lore.py`, `core/region.py`, `core/world.py` for state machines and cross-linking logic; the `mcp/` tool docstrings/signatures for the exact tool surface; `cac <module> --help` output for the CLI-fallback surface; and the current `.claude/skills/world-manager` and `.claude/skills/campaign-manager` `SKILL.md` files for the lifecycle procedure as currently documented (review gate steps, prime disclosure ladder, etc.).
4. Write the draft, then run the verification pass described below before considering the encounter ready for review.

## Verification

Cross-check the drafted guide against three ground truths and reconcile any mismatch before this encounter is considered done:

1. **Skills** — re-read `.claude/skills/world-manager/SKILL.md` and `.claude/skills/campaign-manager/SKILL.md` in full; confirm every lifecycle transition, gate, and cross-link the guide describes matches what those files actually say agents must do.
2. **MCP tools** — enumerate the actual `mcp__crypts-and-commits__*` tool set (via the `mcp/` source modules or the live tool list) and confirm the guide's description of available operations per content type matches reality, with no invented or missing tools.
3. **CLI help** — spot-check `cac <module> --help` (and relevant subcommand `--help`) output for each of `world`, `lore`, `region`, `campaign`, `encounter` and confirm the guide's CLI-fallback framing is consistent with it.

This is a documentation cross-check, not an automated test — there is no pass/fail script. If the check surfaces a discrepancy between the skills, the MCP tools, the CLI, or between any of those and the drafted guide, do not silently resolve it in either direction (i.e. don't just edit the guide to match code, or vice versa) — stop and review the gap together with the user to decide the correct resolution before finalizing the document.

Standard repo hygiene still applies: `pdm run pytest -q` and `pdm run ruff check .` / `ruff format .` clean, per the `clean-tests-and-lint` world lore, even though this encounter's main content is a markdown file with no direct test coverage of its own.

## Log

### Review - 2026-07-28T03:21:26Z - John Hoff

Reviewed against the three lore items resolved by prime_applicable_lore (clean-tests-and-lint, cli-mcp-parity, console-best-practices): the Plan is consistent with all three — it explicitly commits to the pytest/ruff gate in Verification, and neither of the region-scoped CLI/console lore items is triggered since this encounter adds only a packaged markdown template (core/templates/docs/workflow.md) with no CLI or rich.Console changes. No conflicts found. One non-blocking note: the Plan doesn't mention test coverage for the new templates/docs/ subpackage (e.g., an importlib.resources load check mirroring coverage of the existing template subpackages); this isn't a lore violation but worth confirming isn't an oversight before this moves to open. Passing with notes.

### Message - 2026-07-28T03:22:42Z - John Hoff

Per reviewer note: include test coverage for the new `templates/docs/` subpackage as part of this encounter's execution — add a test verifying `docs/workflow.md` loads via `importlib.resources`, mirroring existing coverage of the `templates/sourcebook/` and `templates/skills/` template subpackages, rather than leaving the new template subpackage uncovered.

### Message - 2026-07-28T03:39:23Z - John Hoff

Scope deviation from the locked Requirements: the Requirements explicitly excluded "worked examples of ideal agent-user interaction flows" as a follow-on extension. Per the developer's direction, this is being pulled forward into the current pass - adding one concrete example section to workflow.md walking an encounter from conversation through creation, review, execution, and completion, to the eventual git commit. Scope otherwise unchanged: still describing real, current behavior, not aspirational flow.

### Message - 2026-07-28T03:41:30Z - John Hoff

Further scope addition per the developer: a second new section, "Explicit user gates," documenting the encounter lifecycle's codified approval checkpoints (pre-review spawn, reviewed->open, open->completed) as their own standalone reference rather than only implicitly within the per-type Encounter section and the conversation-to-commit example.

### Completed - 2026-07-28T04:02:41Z - John Hoff

Workflow Reference Guide shipped at packages/crypts-and-commits/src/cac/core/templates/docs/workflow.md, covering all five sourcebook types, their status lifecycles (with Mermaid diagrams for campaign/encounter), cross-type connections, an explicit-user-gates reference, and a conversation-to-commit worked example. Verified against the current skills, MCP tool set, and CLI help output - no discrepancies found. Test coverage added (test_templates.py) and pdm run pytest -q / ruff check / ruff format all clean. Two new region lore entries (workflow-doc-source-of-truth, skills-authored-only-in-templates) codify the guide as the framework's ongoing source of truth and formalize templates-only skill authorship; CLAUDE.md's prior contradiction on skill hand-editing was corrected to match.
