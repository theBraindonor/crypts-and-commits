---
archived: false
campaign: c009-release-0-4-0-docs
created_by: John Hoff
created_on: '2026-11-24T02:05:56Z'
encounter: null
history: []
name: c009-e000-delete-c003-working-notes
origin: Developer (GM), c009 chartering after the 0.4.0 pre-release review
resolution: null
status: recorded
summary: Delete the c003 working notes docs/workflow-guide-split-design.md and docs/workflow-context-update-proposal.md
  rather than archiving or relabeling them.
updated_by: John Hoff
updated_on: '2026-11-24T02:05:56Z'
---

## Decision

Delete `docs/workflow-guide-split-design.md` and `docs/workflow-context-update-proposal.md` as part of the 0.4.0 release documentation campaign, to keep the repository clean.

## Context

Both files were working artifacts of c003 (workflow guide split). The design document still described itself as not replacing the packaged workflow's authority, which became stale once the split shipped. The pre-release review offered three options: archive, delete, or add a historical header. Nothing outside the sourcebook links to either file.

## Consequences

The design rationale and approved text remain recoverable from Git history and from c003's encounters and rulings (notably `c003-e001-self-contained-guides-mcp-headroom` and `c003-e002-workflow-authority-and-world-routing`). Future campaign working notes have no standing home under `docs/` by default.
