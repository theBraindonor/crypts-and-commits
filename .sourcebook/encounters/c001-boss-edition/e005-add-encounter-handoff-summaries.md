---
archived: false
campaign: c001-boss-edition
created_by: John Hoff
created_on: '2026-10-27T05:06:54Z'
depends_on: []
kind: scripted
name: e005-add-encounter-handoff-summaries
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-10-27T05:14:56Z'
---

## Requirements

- Require a brief user-facing summary after an encounter is drafted, before requesting independent review. Identify the encounter and its draft status, explain its intended outcome, scope, main planned changes, and verification approach, and provide a link or reference to the full encounter so the developer can choose whether to read it.
- Require a brief user-facing summary after every independent encounter review, including PASS-WITH-NOTES, REJECT, and NOT-REVIEWABLE. Report the verdict, material findings (or their absence), and their practical impact on scope, approach, risks, verification, or readiness. Distinguish proposed changes from changes actually made and state the resulting encounter status.
- Include an explicit, reasoned recommendation to proceed or revise in light of the review. For a passing review, explain any remaining notes or conditions; for a rejected or non-reviewable draft, explain what needs revision or clarification before a fresh review. Recommendations inform the developer's decision and do not authorize opening or executing an encounter.
- Keep both summaries concise and decision-oriented, with enough substance to decide whether to inspect the full encounter. Cover both scripted and unscripted encounters, adapting draft summaries to recorded work when no Plan/Verification exists.
- Implement this behavior in the packaged Codex campaign-manager skill and document the Codex-specific handoff guidance in the canonical Workflow Reference Guide. The Claude skills already provide the desired behavior and must remain unchanged. Preserve independent reviewer isolation, review-message fidelity, automatic transition on PASS-WITH-NOTES, and all existing user approval gates.
- This is skill guidance and documentation work; no new stored summary fields, CLI/MCP operations, or encounter lifecycle changes are required.

## Rationale

During this campaign, Codex has provided less useful handoff information than the developer typically sees with Claude. A short draft summary lets the developer assess the proposed work before deciding whether to read the full encounter or authorize independent review. A short review summary should explain both what the reviewer found and what those findings mean, then give a clear recommendation. Explicit Codex guidance makes these checkpoints predictable across future Codex sessions. Claude already provides the desired behavior; this encounter targets the Codex gap.

## Plan

1. Inspect the draft and review handoffs in the canonical guide at `packages/crypts-and-commits/src/cac/core/templates/docs/workflow.md` and the packaged Codex skill template at `packages/crypts-and-commits/src/cac/core/templates/skills/codex/campaign_manager/SKILL.md`. The Claude counterpart at `packages/crypts-and-commits/src/cac/core/templates/skills/claude/campaign_manager/SKILL.md` may be read as a reference for the desired behavior, but must not be edited.
2. Update the Workflow Reference Guide with the Codex-specific draft-summary and review-summary content and timing, without changing Claude's procedure. Include an explicit proceed-or-revise recommendation, full-encounter access, and concise examples showing the difference between reviewer findings, their impact, and actions actually taken.
3. Update only the packaged Codex campaign-manager skill to implement that guidance. Place the draft summary before the request to spawn an independent reviewer, and the review summary after handling the verdict under the existing lifecycle rules. Include meaningful guidance for passing reviews, rejected or non-reviewable drafts, revised drafts awaiting renewed review approval, and unscripted records. Do not substitute the conversational summary for the reviewer's recorded message or alter the fresh-reviewer prompt's isolation.
4. Check consistency with `docs/boss-edition.md`, this campaign's design reference, and reconcile any directly conflicting statements there in the same change. Keep this encounter focused on the two handoffs rather than the broader Boss Edition skill rewrite.
5. Edit only packaged sources, never deployed `.agents/skills/` or `.claude/skills/` copies. Preserve unrelated work already present, including changes to the workflow guide. Tell the developer to run `cac bootstrap init` to deploy updated templates; the assistant must not run bootstrap.

## Verification

- Compare the canonical guide's Codex guidance and the packaged Codex campaign-manager skill to confirm they consistently require both summaries and a reasoned proceed-or-revise recommendation. Confirm no Claude skill templates were changed.
- Walk through representative scripted and unscripted draft handoffs, PASS-WITH-NOTES with and without actionable notes, REJECT, and NOT-REVIEWABLE. Confirm each handoff exposes useful decision context, accurate status, full-encounter access, and appropriate next steps without implying approval.
- Confirm explicit approval remains required before spawning each fresh reviewer and before opening an encounter; passing reviews still auto-transition using the reviewer's proposed message, while rejected/non-reviewable encounters remain draft and require renewed review approval after revision.
- Confirm deployed skill copies were not edited and developer-only redeployment is clearly documented. Use existing template/deployment checks where relevant; add tests only if needed to protect a meaningful existing contract rather than exact prose.
- Run `pdm run pytest -q`, `pdm run ruff check .`, and `pdm run ruff format --check .`; resolve failures before requesting completion. Record results and the developer redeployment step in the completion handoff.

## Log

### Review - 2026-10-27T05:09:10Z - John Hoff

PASS-WITH-NOTES: Independently reviewed the scripted encounter against all five applicable lore bodies. The Plan confines skill edits to the packaged Codex template, updates the canonical workflow guide in the same change, preserves developer-only redeployment, and requires full pytest and Ruff verification before completion. No CLI/MCP parity or console-rendering changes are introduced. No lore conflicts or underspecified scope prevent review. During implementation, ensure examples distinguish reviewer findings, practical impact, proposed actions, and actions actually taken; preserve separate approval gates, exact reviewer-message recording, and correct handling of unscripted encounters. These are implementation checks already covered by the Plan and Verification, rather than required draft revisions.

### Message - 2026-10-27T05:13:16Z - John Hoff

Implementation and verification finished; awaiting developer confirmation before completion. Updated only the packaged Codex campaign-manager skill and the Codex-specific section of the canonical workflow guide. Draft handoffs summarize intent, scope, changes, verification, and full-encounter access; review handoffs summarize verdict, findings, impact, actual versus proposed actions, resulting status, and a reasoned proceed-or-revise recommendation. Checked scripted and unscripted drafts, passing reviews with and without actionable notes, rejected/non-reviewable drafts, and renewed-review handoffs. Preserved all explicit user gates, reviewer isolation and prompt, recorded-message fidelity, automatic passing-review transitions, Claude templates, deployed skills, and unrelated existing changes (including the world-branch-settings section in workflow.md). No conflict with docs/boss-edition.md required a design update. Focused skill/docs tests: 22 passed. Full pytest: 1012 passed. Ruff check: passed. Ruff format --check: 227 files already formatted. The initial focused check caught MCP workflow-guide truncation at the 40,000-character budget; condensed only the new examples and confirmed the full-body MCP test passes without changing budgets. Developer follow-up: run pdm run cac bootstrap init to deploy the updated template; the assistant did not run bootstrap.

### Message - 2026-10-27T05:14:33Z - John Hoff

Developer reported running bootstrap. Verified all four deployed Codex/Claude campaign-manager and world-manager skill files match their respective packaged templates after normalizing line endings. Confirmed the deployed Codex campaign-manager contains Draft handoff and Review handoff sections, practical review impact, an explicit proceed-or-revise recommendation, renewed-review approval handling, and the completion confirmation gate. Redeployment verified; encounter remains open pending developer completion confirmation.

### Completed - 2026-10-27T05:14:56Z - John Hoff

Completed with developer approval. Codex draft/review handoff guidance implemented and documented; independent review passed, 1012 tests and Ruff checks passed, and developer bootstrap deployment was verified against all four packaged skill templates.
