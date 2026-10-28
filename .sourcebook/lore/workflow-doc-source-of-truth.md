---
assigned_regions:
- crypts-and-commits
assigned_to_world: false
created_by: John Hoff
created_on: '2026-07-28T03:52:44Z'
enabled: true
name: workflow-doc-source-of-truth
summary: workflow.md and tool-reference.md are a paired source of truth. workflow.md
  owns the domain model, lifecycles/guards, cross-type connections and skill procedure;
  tool-reference.md owns MCP/CLI names, arguments, result shapes, errors, budgets
  and continuation. A substantive change updates the owning doc(s) in the same change.
  Check when a Plan touches mcp/, cli/, core/ or a skill template.
updated_by: John Hoff
updated_on: '2026-10-28T03:36:01Z'
---

# Workflow Guide and Tool Reference Are the Framework's Source of Truth

Two packaged documents under
`packages/crypts-and-commits/src/cac/core/templates/docs/` form a paired
source of truth. Each statement has exactly one owner:

- **`workflow.md`** (the Workflow Reference Guide) owns the `.sourcebook`
  domain model's structure, status lifecycles and their guards and
  restrictions, cross-type connections, and the workflow procedure that the
  `world-manager`, `world-planner` and `campaign-manager` skills are authored
  against: approval gates, the review flow, the disclosure ladder, and the
  planning, campaign and branch procedure.
- **`tool-reference.md`** (the Tool Reference) owns MCP tool and CLI command
  names, arguments and options, result and identity shapes, error and guard
  conditions as surfaced by a tool, response budgets, and cursor
  continuation.

Any substantive change to one of the following must update the document that
owns the affected statement, in the same change, not as a follow-up. A change
that touches both kinds of statement updates both documents.

- An MCP tool's behavior, name, arguments, or return shape (`mcp/*.py`) -
  usually tool-reference.md, plus workflow.md if the rule it enforces changes.
- A CLI command's behavior, name, or arguments (`cli/*.py`), including any
  new CLI-only command exempted from MCP parity by `cli-mcp-parity` -
  usually tool-reference.md.
- A status lifecycle transition, guard, or restriction in `core/*.py`
  (e.g. what's allowed at each status, what requires a message, what locks
  content) - workflow.md, plus tool-reference.md where a tool's errors or
  results change.
- A cross-type connection (e.g. what's bidirectional vs. one-directional,
  what carries a status restriction) - workflow.md.
- The `world-manager`/`world-planner`/`campaign-manager` skill procedure
  itself - approval gates, the review flow, the disclosure ladder, planning
  and branch procedure - wherever that procedure is described in prose (see
  `skills-authored-only-in-templates` for where that prose actually lives) -
  workflow.md.

A "substantive" change is one that would make an existing statement in
either document inaccurate - a wording/typo fix or a purely internal refactor
with no observable behavior change does not require an update.

When reviewing any encounter whose Plan touches `mcp/`, `cli/`, `core/`, or
any skill's `SKILL.md` template: confirm the Plan or Verification includes
updating the owning document(s) to match, or explicitly justifies why no
update is needed. Treat a missing update as a lore violation, the same way
`cli-mcp-parity` treats a CLI command added without its MCP counterpart.
