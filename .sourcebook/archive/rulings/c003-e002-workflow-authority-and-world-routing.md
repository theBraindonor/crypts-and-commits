---
archived: true
campaign: c003-workflow-guide-split
created_by: John Hoff
created_on: '2026-11-21T05:31:55Z'
encounter: e002-implement-phase-workflows
history:
- action: canonize
  by: John Hoff
  message: 'Canonized during planning triage on 2026-11-21. The approved changes were
    applied through MCP during c003/e002 and verified as current: lore workflow-doc-source-of-truth''s
    body and summary were replaced to give planning-workflow and development-workflow
    phase ownership, with primary homes and synchronized mirrors, workflow.md as a
    routing index and tool-reference.md as contract owner. The world summary gained
    the routing sentence for the planning-workflow/development-workflow docs, workflow
    as index, tool-reference, branching-guide and migration-guide. The crypts-and-commits
    region needed no text change.'
  'on': '2026-11-21T06:24:58Z'
name: c003-e002-workflow-authority-and-world-routing
origin: Developer (John Hoff), approving exact c003/e002 context-update proposal
resolution: 'Canonized during planning triage on 2026-11-21. The approved changes
  were applied through MCP during c003/e002 and verified as current: lore workflow-doc-source-of-truth''s
  body and summary were replaced to give planning-workflow and development-workflow
  phase ownership, with primary homes and synchronized mirrors, workflow.md as a routing
  index and tool-reference.md as contract owner. The world summary gained the routing
  sentence for the planning-workflow/development-workflow docs, workflow as index,
  tool-reference, branching-guide and migration-guide. The crypts-and-commits region
  needed no text change.'
status: canonized
summary: Approve phase-specific workflow authority with primary owners and synchronized
  shared copies, retaining workflow as an index and tool-reference as contract owner.
  Approve the matching world-summary routing sentence; the region needs no text change.
updated_by: John Hoff
updated_on: '2026-11-21T06:25:05Z'
---

## Decision

The developer approved the exact replacement body and summary for workflow-doc-source-of-truth and the single world-summary routing sentence presented in docs/workflow-context-update-proposal.md.

## Context

The implemented split provides planning-workflow and development-workflow as self-contained phase guides and workflow as a short index. The previous lore named workflow as the monolithic procedural authority, and the world summary listed it as a detailed reference. Both needed alignment. The crypts-and-commits region text contains no stale routing and its lore assignment remains valid.

## Consequences

Planning owns static context, bosses, triage, priming, synchronization/numbering and collision checks; development owns campaign/coupling/reconciliation, encounters, gates and capture. Every substantive change updates its primary section and every affected mirror in the same change. Primary ownership is for authoring/reconciliation, not an extra routine retrieval. Tool-reference remains the contract owner. The shared actions-not-separately-gated paragraph stays in both phases with existing authorization qualifications. No existing developer approval gate is waived. The approved lore/world changes were applied through MCP and read back successfully. Template redeployment remains developer-run, and the persistent MCP consumer needs reconnect to load the registry.
