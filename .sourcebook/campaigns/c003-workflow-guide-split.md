---
archived: false
bosses:
- b006-split-workflow-guide-by-phase
created_by: John Hoff
created_on: '2026-11-21T04:47:41Z'
name: c003-workflow-guide-split
status: completed
updated_by: John Hoff
updated_on: '2026-11-21T05:38:17Z'
---

# Workflow Guide Split

## Objective

Deliver b006-split-workflow-guide-by-phase: registered development-workflow and planning-workflow guides that are significantly smaller than the combined workflow, with an enforced 40,000-character cap for each workflow guide. Retain workflow as a short routing entry point. Preserve lifecycle rules, approval gates and procedural authority.

## Tactical Approach

1. Map the existing workflow's rules and consumers to planning, development and shared concerns. Compare concrete outlines with consistent duplication against a common-workflow section or guide. Measure likely size and assess retrieval/routing clarity with the developer before choosing the shipped structure. This is a campaign experiment, not a prerequisite left to planning.
2. Implement the chosen guide split, registration and retrieval, restore 40,000-character per-guide limits, and add focused verification of names, limits and references. Preserve all existing rules and gates; use a coverage map and logical review rather than prose-mirroring tests as proof of semantic continuity.
3. Update all six packaged skill templates, tool-reference/branching/migration cross-references and affected public or repository guidance. Update workflow-doc-source-of-truth lore through approved world-manager tools with developer approval of its body/summary. Deployed skills are developer-redeployed, not edited by the assistant.
4. Jointly review the result for logical consistency, routing and duplicated/shared procedure. Address material findings, run the full test suite and ruff, then request campaign completion confirmation with a postmortem.

## Encounter Strategy

Draft a bounded first encounter for source/consumer inventory and concrete split experiments, producing a recommendation for joint review. Draft subsequent implementation and integration encounters from its findings; assign the crypts-and-commits region and relevant dependencies. Each encounter keeps separate developer approval for fresh independent review, opening and completion. Registration/opening of this campaign does not authorize any encounter's execution.

## Verification and Completion

Joint developer/assistant consistency review and clean automated checks support completion. Tests cover retrieval/registration, cross-references and per-guide size caps; pdm run pytest -q and ruff must pass. Practical validation cannot be fully completed in this campaign and will accumulate organically through actual usage in later fresh sessions; it is not a completion gate. Record later findings as rumors for planning.

## Boundaries and Decisions

Only b006 is selected. b004 description accuracy and b003 integrity behavior stay outside scope. The names development-workflow and planning-workflow and 40,000-character caps are settled. A common-workflow section/guide is optional and will be decided from campaign experiments and joint review. Consistent duplication is acceptable. No lifecycle or approval-policy changes are intended.

## Integration Context

Registration starts from local main containing accepted planning commit a736b85. Remote refs were refreshed: origin/main is one commit behind local main, and no c003 reservation was observed. This campaign is local until explicit publication is requested. Assignment registration integrates into local main before opening on the matching execution branch.

## Log

### Completed - 2026-11-21T05:38:17Z - John Hoff

Completed b006 through two developer-confirmed encounters: e001 compared concrete duplicate/common allocations and established the accepted self-contained structure; e002 implemented and reviewed the split. Delivered planning-workflow (31,694 LF characters), development-workflow (32,482) and workflow routing index (761), each under the restored 40,000-character cap for broad MCP compatibility headroom. Shared content remains synchronized with explicit primary owners; tool-reference remains the contract owner. Registry, CLI/MCP descriptions, six packaged skill templates, supporting guides, public/local references and approved lore/world routing are aligned. No lifecycle or approval policy changed. Final checks: 1722 tests passed, Ruff lint clean, format 328 files unchanged, diff whitespace clean; checked 48 relative links/fragments and preserved 48 allocated source-slice/copy placements. Developer bootstrap completed; all six deployed skills match templates byte-for-byte; the connected MCP consumer serves the index and both phase guides untruncated. Both encounters are completed, inventories show no numeric identity collisions, and campaign/b006 ownership reciprocates without diagnostics. Joint review accepted the outcome. Lesson: allocating whole sections missed a planning-relevant exception paragraph even after independent design review; Claude's feedback corrected it, and a focused regression now ensures both phases retain the complete 'Not separately gated' rule and authorization qualifications. Future actual-use validation will accumulate organically, with findings captured as rumors rather than blocking completion. Scope stayed on b006; b003 and b004 remain separate. Implementation is completed locally on c003-workflow-guide-split but still uncommitted/unmerged; campaign completion does not establish Git integration or authorize publication.
