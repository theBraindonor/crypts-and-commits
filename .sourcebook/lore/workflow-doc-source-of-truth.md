---
assigned_regions:
- crypts-and-commits
assigned_to_world: false
created_by: John Hoff
created_on: '2026-07-28T03:52:44Z'
enabled: true
name: workflow-doc-source-of-truth
summary: planning-workflow.md and development-workflow.md own phase procedure; workflow.md
  is a routing index. tool-reference.md owns MCP/CLI contracts. Each rule has a primary
  home; shared copies stay synchronized in the same substantive change. Review lifecycles,
  guards, connections and skill procedure against the owning guide and affected mirrors.
updated_by: John Hoff
updated_on: '2026-11-21T05:31:37Z'
---

# Workflow Guides and Tool Reference Are the Framework's Source of Truth

Packaged documents under
`packages/crypts-and-commits/src/cac/core/templates/docs/` have distinct roles:

- `planning-workflow.md` owns static context, boss lifecycle/readiness,
  dependencies and roadmap adoption; rumor/ruling record semantics and triage;
  priming, synchronization, numbering, collision checks and planning-side archival.
- `development-workflow.md` owns campaign lifecycle, selection and coupling,
  reconciliation, encounter lifecycle, approval gates, independent review,
  Codex handoffs and capture/execution procedure. The rule on actions not
  separately gated has its primary home here and a full matching copy in planning.
- `workflow.md` is a short task router, not the full procedural authority.
- `tool-reference.md` owns MCP/CLI names, arguments/options, result and identity
  shapes, errors and guards as surfaced by tools, budgets and continuation.

Shared rules are repeated so ordinary phase work needs one deep-guide retrieval.
Each rule has one primary home for authoring and reconciliation; every affected
mirror must change in the same substantive change. An accidentally divergent
mirror is a documentation defect: reconcile against the primary rule and the
implementation and correct all affected copies. Primary ownership does not
require readers to fetch both guides during ordinary work.

Any substantive change must update its owning document and affected mirrors in
the same change, not as a follow-up:

- MCP/CLI behavior, names, arguments or results: tool-reference, plus the owning
  phase workflow when procedural meaning changes. CLI/MCP parity still applies.
- Core lifecycle transitions, guards, restrictions and cross-type connections:
  the owning phase workflow and mirrors, plus tool-reference when surfaced
  errors or result contracts change.
- Skill procedure, including all approval gates, independent review, disclosure,
  planning, branching and execution: the owning phase workflow and mirrors.
  Skill text is authored only in packaged templates; the developer redeploys it.

For statements spanning phases, planning is primary for context, bosses, triage,
synchronization/numbering and collision checks; development is primary for
campaign/coupling/reconciliation, encounters, gates and capture. Planning owns
maintenance detail, with migration-guide owning upgrade/migration instructions.
The phase guides retain prohibitions on agent-run bootstrap and index rebuild.
The three separate encounter approvals remain fully stated in development and
inline in both campaign-manager templates; shared authorization exceptions never
waive the developer approvals required for context edits.

A substantive change makes an existing statement inaccurate; a typo correction
or internal refactor with no observable behavior change does not require a
procedural update. Both types of statement may change together, requiring both
procedural and contract updates.

When reviewing a Plan touching mcp/, cli/, core/ or a skill template, confirm
that the owning guides and affected mirrors are updated, or that the Plan
explicitly justifies why no update is needed. Missing updates are lore violations.
