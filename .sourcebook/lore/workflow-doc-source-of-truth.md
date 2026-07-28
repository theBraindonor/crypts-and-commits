---
assigned_regions:
- crypts-and-commits
assigned_to_world: false
created_by: John Hoff
created_on: '2026-07-28T03:52:44Z'
enabled: true
name: workflow-doc-source-of-truth
summary: workflow.md is the framework's source of truth for the .sourcebook domain
  model and skill procedure. Any substantive change to an MCP tool, CLI command, status
  lifecycle, cross-type connection, or skill procedure must update workflow.md in
  the same change. Check when an encounter's Plan touches mcp/, cli/, core/, or a
  skill template.
updated_by: John Hoff
updated_on: '2026-07-28T03:53:01Z'
---

# Workflow Document Is the Framework's Source of Truth

`packages/crypts-and-commits/src/cac/core/templates/docs/workflow.md` (the
"Workflow Reference Guide") is the single source of truth for the
`.sourcebook` domain model's structure, status lifecycles, and cross-type
connections, and for the workflow procedure (approval gates, review flow)
that implementation-specific agent skills are authored against.

Any substantive change to one of the following must update this document in
the same change, not as a follow-up:

- An MCP tool's behavior, name, arguments, or return shape (`mcp/*.py`).
- A CLI command's behavior, name, or arguments (`cli/*.py`), including any
  new CLI-only command exempted from MCP parity by `cli-mcp-parity`.
- A status lifecycle transition, guard, or restriction in `core/*.py`
  (e.g. what's allowed at each campaign/encounter status, what requires a
  message, what locks content).
- A cross-type connection (e.g. what's bidirectional vs. one-directional,
  what carries a status restriction).
- The `world-manager`/`campaign-manager` skill procedure itself - approval
  gates, the review flow, the disclosure ladder - wherever that procedure is
  described in prose (see `skills-authored-only-in-templates` for where that
  prose actually lives).

A "substantive" change is one that would make an existing statement in
workflow.md inaccurate - a wording/typo fix or a purely internal refactor
with no observable behavior change does not require an update.

When reviewing any encounter whose Plan touches `mcp/`, `cli/`, `core/`, or
either skill's `SKILL.md` template: confirm the Plan or Verification includes
updating workflow.md to match, or explicitly justifies why no update is
needed. Treat a missing update as a lore violation, the same way
`cli-mcp-parity` treats a CLI command added without its MCP counterpart.
