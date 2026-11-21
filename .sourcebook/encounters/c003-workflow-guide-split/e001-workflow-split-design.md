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
status: completed
updated_by: John Hoff
updated_on: '2026-11-21T05:09:38Z'
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

## Log

### Review - 2026-11-21T04:51:42Z - John Hoff

PASS-WITH-NOTES: Reviewed the scripted Plan against all five applicable lore bodies. The design-only scope preserves current workflow/tool-reference authority, changes no CLI/MCP or console behavior, protects deployed skills and reserves redeployment for the developer. Verification includes the required full pytest and Ruff checks without bypasses. Coverage mapping, reproducible candidate sizes and retrieval walkthroughs provide concrete review evidence without claiming practical usability validation. If required check fixes exceed the sole design-artifact scope, reconcile that scope before making those changes. No lore conflicts or flagged-but-unverified concerns found.

### Opened - 2026-11-21T04:53:20Z - John Hoff

Developer approved opening and execution after independent PASS-WITH-NOTES review.

### Message - 2026-11-21T04:58:09Z - John Hoff

Execution deliverable: docs/workflow-guide-split-design.md contains complete section allocation, two concrete outlines, a reproducible in-memory allocation experiment, desk retrieval walkthroughs, primary-authority/duplication treatment, consumer/test inventory and suggested follow-up encounters. Baseline workflow is 43,253 LF characters; retained groups P=11,642, D=12,594, S=17,683. Candidate A planning/development slices total 29,325/30,277; estimated with 1,000-character wrappers 30,325/31,277. Candidate B extracts 17,683 shared characters into common-workflow. Recommendation is Candidate A initially, subject to joint developer review and structural decision. Embedded Python reproduction executed successfully with all coverage/length assertions. Verification: pdm run pytest -q => 1702 passed in 133.83s; pdm run ruff check . => all checks passed (nonblocking cache write warning); pdm run ruff format . => 322 files left unchanged. git status confirms the design document is the sole ordinary-file change; only this encounter's lifecycle/log changed through MCP. No shipped guide, runtime, test, template, deployed skill or lore edits. Joint developer consistency review and structural choice remain pending, as does explicit completion confirmation. No fresh-session usage validation was performed or required.

### Message - 2026-11-21T04:59:46Z - John Hoff

Developer accepted Candidate A after joint design review: two self-contained phase guides with consistent shared duplication and no common guide initially. Clarified that the 40,000-character cap is primarily for broad compatibility/headroom under MCP call character limits, not minimizing stored duplication. Updated the design artifact's acceptance status and rationale; recorded c003-e001-self-contained-guides-mcp-headroom. No source allocation or executable reproduction code changed. Explicit encounter completion confirmation remains pending.

### Message - 2026-11-21T05:03:48Z - John Hoff

At the developer's explicit request, a fresh independent subagent compared the design deliverable against current packaged guides, all six skill templates, registry/docs/skills tests, cited consumers and the recorded design ruling. No material inconsistencies found. The subagent independently executed the reproduction block and confirmed all allocations/arithmetic and current-versus-future scope. One nonblocking clarification was added to the design: substantive rule changes update primary and every affected mirror in the same change; primary ownership is for authoring/reconciliation, not a mandatory second guide retrieval; divergent mirrors are documentation defects to reconcile. Review limits: no broad test rerun, no implemented-guide measurements or actual fresh-session/client compatibility validation. A newly observed untracked .claude/settings.local.json is unrelated to this encounter and left untouched; the design artifact remains the only ordinary-file deliverable authored here. Completion still awaits developer confirmation.

### Message - 2026-11-21T05:03:55Z - John Hoff

Clarification to the preceding review log: the reviewer reported an untracked .claude/settings.local.json, but the parent's final git status does not list it. Its provenance/status was not established. The parent made no changes to that path; current visible changes are the design artifact and this encounter/ruling's MCP-managed records.

### Message - 2026-11-21T05:08:54Z - John Hoff

Developer relayed Claude's valid coverage finding: the development-only Explicit user gates source section contains a cross-phase 'Not separately gated' paragraph covering context edits used during planning. Corrected the design allocation by extracting that exact 335-character paragraph as shared; both phase guides must carry a matching copy with a locally valid authorization cross-reference. Kept the three encounter gates and review flow development-only, with planning routing there for encounter work. Added explicit ownership/mirror and cross-phase exception checks so no blanket authorization is inferred. Updated outlines, retrieval walkthrough, arithmetic and reproduction code. Reproduction passed: P=11,642, S=18,018, D=12,259; Candidate A=29,660/30,277 retained characters, estimated 30,660/31,277 including wrappers. This supersedes the earlier allocation figures and the independent report's no-material-inconsistency conclusion on cross-phase exception coverage. Only design prose and its embedded allocation reproduction changed; no shipped guides/code/tests/templates/lore modified. Full suite/Ruff results from prior verification remain applicable to unchanged implementation; reran the changed allocation calculation successfully. Encounter remains open for joint review and completion confirmation.

### Completed - 2026-11-21T05:09:38Z - John Hoff

Developer confirmed completion after joint review, independent deliverable consistency check and correction of Claude's cross-phase 'Not separately gated' coverage finding. Delivered docs/workflow-guide-split-design.md with accepted self-contained phase-guide structure, explicit synchronized ownership, complete allocation map, consumer inventory and reproducible measurements. Revised estimates including wrapper allowances: planning 30,660; development 31,277, each below the 40,000-character compatibility cap. Reproduction checks passed after the correction; implementation unchanged, with prior verification 1702 tests passed, Ruff lint clean and 322 files left unchanged by formatting. Fresh-session usage validation remains organic and is not a completion gate. Follow-up implementation remains in open c003; this completes only the design encounter.
