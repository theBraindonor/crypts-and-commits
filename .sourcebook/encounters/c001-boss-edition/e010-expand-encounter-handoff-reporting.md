---
archived: false
campaign: c001-boss-edition
created_by: John Hoff
created_on: '2026-10-27T17:25:55Z'
depends_on:
- e005-add-encounter-handoff-summaries
kind: scripted
name: e010-expand-encounter-handoff-reporting
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-10-27T17:42:42Z'
---

## Requirements

- Replace the deliberately brief Codex draft and review handoff guidance introduced by `c001/e005` with substantive, decision-oriented reports. Each report must stand on its own well enough for the developer to understand the proposed work or review outcome and make the next decision without opening the full encounter.
- Before requesting independent review, identify the encounter, campaign, kind, and draft status; explain the problem and motivation, intended behavior or outcome, scope and boundaries, main implementation steps and affected areas, significant choices and tradeoffs, risks and unresolved questions, and the verification approach with concrete success criteria. For unscripted encounters, explain the work already performed, its rationale, evidence, and remaining follow-up instead of inventing a future Plan or Verification.
- After every independent review, report the verdict and review coverage; explain each material finding with its reasoning or supporting evidence, practical impact, and recommended response. Explicitly distinguish blocking issues, actionable notes, and flagged-but-unverified concerns, and say when none exist. Explain what was actually changed or recorded versus what remains proposed, remaining risks or uncertainty, resulting status and locking implications, and a reasoned recommendation to proceed or revise with remaining conditions and the next approval needed.
- Use several developed paragraphs or grouped bullets appropriate to the encounter's complexity. Remove instructions that reduce these reports to a short paragraph, a few bullets, or a brief summary. Prioritize useful explanation over a fixed word count, exhaustive repetition of every lore check, or padding. A report must explain why the details matter rather than merely listing topic labels. Retain a full encounter reference for deeper inspection.
- Cover scripted and unscripted encounters, passing reviews with and without actionable notes, rejected and non-reviewable drafts, and revised drafts awaiting renewed review approval. Revised-draft reports must identify what changed, why, and which concerns remain.
- Limit implementation to the packaged Codex campaign-manager skill and the matching Codex-specific guidance in the canonical Workflow Reference Guide. Preserve Claude behavior, the independent reviewer's prompt and isolation, the reviewer's recorded message, automatic transition on PASS-WITH-NOTES, and every existing explicit approval gate.
- No new stored report fields, CLI/MCP operations, response budgets, or encounter lifecycle changes are required.

## Rationale

The completed `c001/e005-add-encounter-handoff-summaries` established the correct reporting checkpoints and content categories, but explicitly instructed Codex to be brief. In practice the resulting reports are too short to deliver the context the developer wanted. This follow-up builds on e005's implementation and verification scenarios, retaining its lifecycle safeguards while replacing its brevity target with enough explanation to support an informed decision.

The pre-review report should make the draft understandable before the developer authorizes independent review. The post-review report should make the review's reasoning, consequences, and recommended next action understandable before the developer decides whether to proceed. More useful conversational reporting does not require expanding the independent reviewer's recorded message or changing review mechanics.

## Plan

1. Read `c001/e005` through the encounter interface as historical context. Inspect its current packaged sources: `packages/crypts-and-commits/src/cac/core/templates/skills/codex/campaign_manager/SKILL.md` and `packages/crypts-and-commits/src/cac/core/templates/docs/workflow.md`. Check `docs/boss-edition.md` for directly relevant design constraints. Preserve current content unrelated to this follow-up.
2. Expand the canonical guide's Codex-specific draft and review handoff guidance to define the substantive reports in Requirements. Replace conflicting brevity language and provide representative examples with meaningful reasoning, practical impact, and clear separation of findings, proposed responses, and actions actually taken. Keep shared and Claude-specific procedures unchanged.
3. Update the packaged Codex campaign-manager skill to match. Make the pre-review report precede the request to spawn a reviewer, and the post-review report follow the existing handling of the verdict. Explain how report depth scales with complexity and uncertainty without imposing a hard length quota. Preserve the reviewer prompt, verbatim or faithful recording of its proposed message, automatic passing-review transition, fresh-review approval after rejection, and separate opening and completion approvals.
4. Keep edits confined to packaged sources; do not edit deployed `.agents/skills/` or `.claude/skills/` copies, and do not run bootstrap. Reconcile a directly conflicting statement in `docs/boss-edition.md` only if one exists. Use existing relevant skill deployment and docs checks at `packages/crypts-and-commits/tests/core/test_skills.py`, `packages/crypts-and-commits/tests/core/test_docs.py`, and `packages/crypts-and-commits/tests/mcp/test_docs.py`; confirm exact tests before running.
5. Walk through the representative handoffs below, run required checks, and report the results. Tell the developer to run `pdm run cac bootstrap init` to deploy the updated template; deployment remains developer-only.

## Verification

- Compare the packaged Codex skill and canonical guide: both require independently understandable, substantive pre-review and post-review reports, with no conflicting short/brief report instructions. Confirm the reviewer prompt, Claude templates, deployed skill copies, lifecycle mechanics, and response budgets remain unchanged.
- Walk through a scripted draft and an unscripted record: verify that the report explains motivation, substance, decisions, uncertainties, and evidence or verification rather than just naming these categories. Confirm a full encounter reference and accurate draft status.
- Walk through PASS-WITH-NOTES with actionable notes and with no actionable notes: verify coverage, finding reasoning, practical consequences, actual versus proposed actions, remaining conditions, reviewed/locked status, and a reasoned recommendation before asking for opening approval.
- Walk through REJECT and NOT-REVIEWABLE, then a revised draft: verify reasons and uncertainty are explained, status remains draft, revisions actually made are identified, unresolved concerns remain visible, and fresh review requires renewed explicit approval. Adapt unscripted reports to the accuracy of recorded work and follow-up rather than implying that already performed work awaits execution.
- Run the narrow existing skill/docs tests first, including MCP workflow-guide retrieval. E005 previously encountered guide truncation at the response budget: keep the guide retrievable under the existing contract by tightening redundant documentation if necessary, rather than increasing budgets or weakening tests. Add tests only for a meaningful uncovered contract, not exact wording.
- Run `pdm run pytest -q`, `pdm run ruff check .`, and `pdm run ruff format --check .`; fix failures and formatting issues before asking for completion. Record results, the manual scenario checks, and the developer-only redeployment step in the completion handoff.

## Log

### Review - 2026-10-27T17:28:30Z - John Hoff

PASS-WITH-NOTES: Independently reviewed scripted encounter c001/e010 against all five applicable lore bodies, its assigned region, the named Codex skill and canonical workflow guidance, the directly relevant design reference, and e005’s historical record. No lore conflicts or missing scope prevent review. The Plan edits packaged skill sources only, updates the canonical workflow guide in the same change, preserves developer-only deployment, and requires full pytest and Ruff checks before completion. No CLI/MCP or console-rendering changes are proposed. During implementation, keep expanded examples focused and verify full workflow-guide retrieval under the unchanged response budget, since e005 previously encountered truncation. Preserve reviewer isolation, message fidelity, automatic passing-review transitions, explicit approval gates, Claude behavior, and unrelated documentation. These are implementation checks already covered by the Plan and Verification; no draft revision is required.

### Message - 2026-10-27T17:31:52Z - John Hoff

Implementation and verification finished; awaiting developer confirmation before completion. Updated only the packaged Codex campaign-manager SKILL.md and Codex encounter handoffs section of the canonical workflow guide. Replaced brevity instructions with substantive reports that stand alone for decisions: motivation, scope, approach, tradeoffs, risks, success criteria, review coverage and limits, finding evidence/reasoning, practical impact, proposed versus actual actions, uncertainty, status, and reasoned next steps. Added developed draft/review examples and guidance for revised and unscripted records, passing reviews with/without actionable notes, REJECT, and NOT-REVIEWABLE. Manual scenario checks confirmed accurate approvals/status and separation of completed work from proposed follow-up. Focused skill/docs tests including CLI/MCP retrieval: 22 passed. Full pytest: 1310 passed. Ruff check passed; Ruff format --check: 254 files already formatted. Full workflow-guide retrieval passes with unchanged budgets. Programmatic normalized comparisons confirmed unchanged reviewer prompt, review gate, later lifecycle rules, and all guide content outside Codex handoffs. No conflict with docs/boss-edition.md required edits. No Claude templates or deployed skills were changed, no bootstrap was run, and unrelated settings were preserved. Developer follow-up: run pdm run cac bootstrap init to deploy the updated template.

### Completed - 2026-10-27T17:42:42Z - John Hoff

Completed with developer approval. Expanded packaged Codex draft/review reporting and canonical workflow examples; independent review passed. Focused tests: 22 passed; full pytest: 1310 passed; Ruff lint and formatting clean. Full workflow-guide retrieval and unchanged reviewer/lifecycle safeguards verified. Developer-only bootstrap deployment remains the follow-up step. Developer authorized completion, commit, and push.
