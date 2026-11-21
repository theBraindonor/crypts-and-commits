---
archived: false
campaign: c003-workflow-guide-split
created_by: John Hoff
created_on: '2026-11-21T04:31:53Z'
depends_on: []
name: b006-split-workflow-guide-by-phase
status: available
summary: Split workflow into development-workflow and planning-workflow, each capped
  at 40,000 characters. Experiment with common-workflow content versus consistent
  duplication. Complete the campaign after joint review and clean automated checks;
  practical validation comes organically through later usage.
updated_by: John Hoff
updated_on: '2026-11-21T04:47:41Z'
---

## Goal

Split the packaged workflow guide into registered `development-workflow` and `planning-workflow` guides, each significantly smaller than the current combined guide and capped at 40,000 characters. Retain `workflow` as a short entry point routing readers to the phase guides.

## Rationale

Promoted from r004-split-workflow-guide-by-phase during planning at the developer's request. Before c002, workflow.md was already about 39,600 characters against a 40,000-character test cap. Ruling procedures required raising that cap to 45,000 as a stopgap (c002-e001-workflow-cap-stopgap). Splitting by phase should restore headroom and reduce the context needed for each working session.

This is a distinct documentation restructuring goal, separate from b004's tool-description accuracy fixes and b003's record-integrity behavior.

## Success Criteria

- Register `development-workflow` and `planning-workflow`, with `workflow` retained as a short entry point identifying the authoritative guidance.
- Planning covers bosses, roadmap adoption, readiness and dependencies, rumor/ruling triage and archival. Development covers campaign selection and registration, encounters, review and approval gates, ruling/rumor capture, completion and review fixes. Cross-phase procedure remains discoverable.
- Preserve existing lifecycle rules, guards and developer approval gates without conflicting statements or omissions. Consistent duplication between phase guides is acceptable.
- Experiment during the campaign with keeping shared procedure in the phase guides versus extracting a `common-workflow` section or guide. Select the final structure from practical trials and joint review; a common guide is not a prerequisite or predetermined outcome.
- All six packaged skill templates (Claude and Codex world-manager, world-planner and campaign-manager) route readers to the appropriate guides.
- The tool reference, branching guide, migration guide and other affected references agree with the new guide structure; workflow-doc-source-of-truth lore is updated through the approved world-manager workflow.
- Restore an enforced 40,000-character cap per workflow guide, including any retained entry point or new common guide. The two phase guides should be significantly smaller than the original combined guide rather than merely fitting under the cap.
- The developer and assistant both review the split for overall logical consistency, preserved procedure, useful routing and coherent duplicated or shared content.
- Automated verification checks registration/retrieval, affected cross-references and size limits; unit tests, the full test suite and ruff are clean.
- Campaign completion requires joint logical-consistency review and clean automated checks. Full practical validation depends on actual usage in fresh working sessions and will accumulate organically after the campaign; it is not a campaign-completion gate. Capture any findings from later usage through the normal rumor and planning workflow.

## Design Notes

Planning decisions confirmed by the developer:

- Guide names: `development-workflow` and `planning-workflow`.
- Some duplication is acceptable to obtain two significantly smaller guides.
- Whether a `common-workflow` section or guide improves the result must be tested during the campaign, when actual layouts and working-session behavior can be compared.
- Restore the size cap to 40,000 characters per guide.
- Campaign verification consists of developer/assistant logical-consistency review and clean automated tests. Final practical validation cannot be fully completed within this campaign: it comes organically through actual usage in later fresh working sessions. Campaign completion must not wait for that ongoing validation.

These decisions establish readiness for campaign selection. The remaining structural experiment belongs to campaign work and does not block availability. No campaign is selected or opened by this record.

## Open Questions / Campaign Experiments

- Does shared procedure work better duplicated consistently in the two phase guides or extracted into a common-workflow section or guide? Decide the shipped structure through campaign experiments and joint review; later organic usage may suggest follow-up refinements.
- Later organic planning and development sessions will exercise discovery, cross-phase routing and preserved approval gates. Their findings inform follow-up work rather than blocking this campaign's completion.
