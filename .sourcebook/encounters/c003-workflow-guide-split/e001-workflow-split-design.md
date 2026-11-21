---
archived: false
campaign: c003-workflow-guide-split
created_by: John Hoff
created_on: '2026-11-21T04:48:50Z'
depends_on: []
kind: scripted
name: e001-workflow-split-design
regions:
- crypts-and-commits
status: draft
updated_by: John Hoff
updated_on: '2026-11-21T04:48:50Z'
---

## Requirements

Produce a concrete, reviewable design for splitting workflow into registered development-workflow and planning-workflow, each significantly smaller than the existing combined guide and capped at 40,000 characters. Retain workflow as a short entry point. Compare consistent duplication with an optional common-workflow section or guide using actual content allocations and sizes. Preserve every lifecycle rule and approval gate.

Deliver an ordinary repository design artifact at docs/workflow-guide-split-design.md with a source-section coverage map, two concrete candidate outlines/content allocations, measured character estimates or prototype measurements, shared-content tradeoffs, affected consumers/tests and a recommended implementation sequence for joint developer/assistant review. The common-content decision remains subject to developer review of the evidence.

This encounter changes only that design artifact, not shipped guides, runtime code, tests, skill templates, deployed skills or managed lore. Later encounters implement the selected structure and approved lore changes.

## Rationale

The old workflow guide's cap was raised to 45,000 characters as a stopgap. Splitting without mapping shared rules risks omissions or conflicting authority; extracting common content too early could also make agents retrieve more documents. b006 deliberately leaves that choice to practical campaign experiments. Concrete allocations and retrieval walkthroughs provide better evidence than deciding from names alone. Final usability validation comes organically after the campaign and is not a completion prerequisite.

## Plan

1. Read the current authoritative source and consumers under packages/crypts-and-commits: src/cac/core/templates/docs/{workflow,tool-reference,branching-guide,migration-guide}.md; src/cac/core/docs.py; src/cac/core/templates/skills/{claude,codex}/{world_manager,world_planner,campaign_manager}/SKILL.md; tests/{core,cli,mcp}/test_docs.py and tests/core/test_skills.py. Inspect repository guidance consumers CLAUDE.md, AGENTS.md, README.md, docs/QUICKSTART.md and packages/crypts-and-commits/README.md. Use CodeGraph first for code and rg scoped to ordinary docs/templates for references; exclude managed .sourcebook contents entirely. Hydrate applicable region/lore via MCP only.
2. Inventory the current workflow's sections/rules and map each to planning, development or shared concerns. Include campaign registration/branch reconciliation, numbering, lifecycle guards, independent review, separate review/open/complete approvals, the disclosure ladder, capture/triage and archival. Record coverage and authority explicitly so the eventual split can be reviewed for omissions.
3. Compare two concrete allocations: (A) two phase guides with consistent shared duplication and (B) phase guides plus a common-workflow section or guide. Keep workflow as the short entry point in both. Use actual source-section lengths or temporary in-memory content assembly to report candidate sizes; label estimates honestly and do not claim finalized guides. Compare retrieval paths for goal planning, campaign registration, encounter review and ruling triage. No fresh agents or separate working sessions are required or launched by this experiment.
4. Write docs/workflow-guide-split-design.md with the evidence, tradeoffs, proposed authoritative homes, affected registrations/references/tests and follow-up encounter boundaries. Identify the future approved update to workflow-doc-source-of-truth lore and developer-run template redeployment; do not edit lore or deployed copies in this encounter. Because only a design artifact is added, the currently owning workflow/tool-reference documents and CLI/MCP contracts remain unchanged and need no same-change substantive update.
5. Present the recommended structure and any unresolved decision to the developer. Record a confirmed design decision as a ruling through the campaign-manager workflow. Do not treat this encounter or its review as authorization to implement later encounters.

## Verification

- Jointly review the design for overall logical consistency: every inventoried rule has a proposed home, fixed guide names and 40,000-character limits are honored, duplicated statements remain consistent and candidate size calculations are reproducible and clearly distinguished from final measurements.
- Check concrete retrieval walkthroughs and consumer inventory; explicitly identify uncertainty rather than claiming fresh-session or practical usability validation.
- Confirm the only ordinary-file change is docs/workflow-guide-split-design.md, with no sourcebook access outside MCP/CLI and no deployed skill edits.
- Run pdm run pytest -q, pdm run ruff check . and pdm run ruff format . from the repository root as required by clean-tests-and-lint. Fix failures without suppressions or weakening tests; preserve unrelated changes. No new unit tests are needed for this design-only artifact.
- Report findings and request developer confirmation before completing the encounter. Later organic usage is not a verification gate.
