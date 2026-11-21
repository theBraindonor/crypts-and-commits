---
archived: false
campaign: c002-rulings
created_by: John Hoff
created_on: '2026-11-21T02:20:44Z'
encounter: e001-ruling-records-core
history: []
name: c002-e001-workflow-cap-stopgap
origin: Developer (GM), during c002/e001-ruling-records-core execution
resolution: null
status: recorded
summary: Raise the workflow.md size cap from 40,000 to 45,000 characters as a stopgap,
  rather than trimming unrelated prose or moving lifecycle text into tool-reference.
  Splitting the guide by phase (r004) is the real fix.
updated_by: John Hoff
updated_on: '2026-11-21T02:20:44Z'
---

## Decision

Raise the doc-test cap on `templates/docs/workflow.md` from 40,000 to 45,000 characters (`test_workflow_leaves_contracts_to_tool_reference_with_headroom`). This is a stopgap. The lasting fix is to split the workflow guide into a development flavor and a planning flavor, captured as rumor `r004-split-workflow-guide-by-phase`.

## Context

`workflow.md` was about 39,600 characters before c002/e001. Even a minimal Rulings section took it to about 40,750. Three options were considered:

- **Raise the cap.** Chosen.
- **Trim unrelated workflow prose.** This would touch text outside e001's scope, and the squeeze would come back in later c002 work.
- **Reduce the workflow Rulings section to a pointer to tool-reference.** This would bend the rule that the workflow guide owns lifecycles.

The developer then suggested the split, which was too large for e001's locked plan.

## Consequences

- The workflow guide is still well under the 64,000-character docs response budget, but it has only about 4,000 characters of headroom. Later c002 work, mainly the ruling capture and triage procedure, will use some of that.
- Once r004 is planned and done, the cap should be revisited and probably lowered for each new guide.
