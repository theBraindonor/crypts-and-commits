---
archived: false
boss: b006-split-workflow-guide-by-phase
created_by: John Hoff
created_on: '2026-11-21T02:11:14Z'
history:
- action: promote
  by: John Hoff
  message: Developer approved a separate boss for the phase-specific workflow guide
    split; scope, success criteria and unresolved design choices are captured in b006.
  'on': '2026-11-21T04:31:57Z'
name: r004-split-workflow-guide-by-phase
origin: Developer (GM), during c002/e001-ruling-records-core execution
resolution: Developer approved a separate boss for the phase-specific workflow guide
  split; scope, success criteria and unresolved design choices are captured in b006.
status: promoted
summary: Split the packaged workflow guide into a development (execution) flavor and
  a planning flavor. The single guide has outgrown its 40,000-character headroom cap,
  and rulings add more procedure.
updated_by: John Hoff
updated_on: '2026-11-21T04:31:57Z'
---

## Observation

`templates/docs/workflow.md` was about 39,600 characters before c002/e001. A doc test caps it at 40,000 characters to keep headroom under the 64,000-character docs response budget. Even a minimal Rulings section pushed it past the cap. During e001 the cap was raised to 45,000 as a stopgap, and that decision is recorded on the encounter. Later c002 work (ruling capture and triage procedure) will add more.

## Suggestion

Split the guide into two flavors:

- a **development** guide: execution, encounters, review gates and capture;
- a **planning** guide: bosses, roadmap, rumor and ruling triage, archival.

Then restore a real headroom cap for each.

## Things a plan would need to settle

- New registered doc names, and whether `workflow` stays as an index.
- Updated `docs_get` references in all six packaged skill templates (claude and codex flavors).
- Updating `workflow-doc-source-of-truth`, which pairs `workflow.md` with `tool-reference.md`.
- The migration-guide and branching-guide cross-references.
- Whether to bring the stopgap cap back down afterward.
