---
archived: false
campaign: c001-boss-edition
created_by: John Hoff
created_on: '2026-10-27T03:36:34Z'
depends_on: []
kind: scripted
name: e001-finalize-boss-edition-design
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-10-27T03:54:32Z'
---

## Requirements

Finalize the implementation contract in `docs/boss-edition.md` for campaign `c001-boss-edition`. The document is already committed (commit `9bd8b87`); preserve that baseline and the decisions it records.

Record a clear disposition for every item under "Remaining implementation details":
- World branch-setting names, defaults, and exposure through world CLI/MCP interfaces.
- Whether archive restoration belongs in this release, distinct from withdrawn -> proposed reactivation.
- Whether editing an available boss returns it to proposed or leaves readiness reassessment to skill guidance.
- The planning skill's final name.
- Search-index handling across branch switches, including how any skill-driven rebuild fits the existing developer-only index-rebuild rule.
- The exact active-boss projection in prime and its response-budget behavior.
- Concrete workflow examples for rejected assignment PRs, abandoning registered drafts before execution, legacy records, and manual integration checks.

For each item, record the decision and rationale, or an explicit deferral with its owning later implementation area and whether it blocks work. Resolve contracts needed before boss storage/lifecycle implementation. Present recommendations and alternatives to the developer; do not label an unresolved proposal as agreed.

Keep the design consistent with the campaign: branch-agnostic endpoints; numbering and branch checks owned by skills; CLI/MCP parity for domain operations; frontmatter-only coupled boss updates; optional freeform rumors; compatibility with historical records. Release numbering and any schema-version change remain explicit decisions for the relevant release/migration work unless needed sooner.

This encounter changes the design document only. Runtime implementation, new public commands, packaged skill/hook changes, deployed artifacts, and sourcebook migration are outside its scope.

## Rationale

The campaign's first tentative step is to establish the design baseline and settle implementation questions before core work. The baseline is already committed, but the remaining proposals affect lifecycle semantics, interfaces, discovery, and compatibility. Recording their disposition now gives later encounters a stable reference without treating the entire design as shipped behavior.

## Plan

1. Read `docs/boss-edition.md` in full and compare its "Decisions established so far", lifecycle, promotion, discovery, compatibility, and remaining-details sections. Read `CLAUDE.md` and `AGENTS.md` for the current repository constraints. Work on the existing `c001-boss-edition` execution branch.
2. Build a decision list in `docs/boss-edition.md`: for each remaining detail, explain the affected contract, a recommended choice, alternatives where material, and whether the decision blocks implementation. Keep proposals clearly marked until the developer resolves them.
3. Discuss the material choices with the developer during execution. Record accepted choices and rationale, update every affected section/table/example in the same document, and retain explicit deferrals with ownership and blocking status.
4. Add practical examples in the design document for the four workflow cases named in Requirements. Examples must preserve developer judgment, the existing approval gates, manual conflict repair, and the limits of locally observed Git state. They describe planned guidance rather than currently available commands.
5. Check the resulting document for contradictions and distinguish established design decisions from unimplemented behavior. No existing CLI/MCP behavior, lifecycle, or skill procedure changes in this encounter, so no update to the canonical `packages/crypts-and-commits/src/cac/core/templates/docs/workflow.md` is required here. Later implementation encounters must update it with each substantive behavior change and ship matching CLI/MCP wrappers. Skill changes belong only in packaged templates; redeployment remains developer-only.
6. Summarize settled decisions, explicit deferrals, and which implementation work can proceed. Keep the encounter open until verification and developer confirmation are complete.

## Verification

- Review the diff of `docs/boss-edition.md`; confirm every remaining implementation detail has a decision or an explicit owned deferral and that all pre-core blockers are settled.
- Cross-check names, defaults, lifecycle transitions, prime projection, search-index policy, workflow examples, and compatibility statements throughout the document against the recorded choices and campaign scope.
- Confirm proposed future behavior remains clearly distinguished from shipped behavior and that no runtime files, packaged/deployed skills or hooks, or managed records were changed to implement the design.
- No new automated tests are needed for this design-only change. Before considering Verification complete, run `pdm run pytest -q`, `pdm run ruff check .`, and `pdm run ruff format .` from the repository root as required by world lore; address failures without suppressing or weakening checks and preserve unrelated user changes.
- Report verification results and remaining deferrals to the developer and obtain confirmation before marking the encounter completed.

## Log

### Review - 2026-10-27T03:39:26Z - John Hoff

Reviewed this scripted encounter against all five applicable lore bodies. The design-only plan is reviewable and consistent with the test/lint gate, CLI/MCP parity, console conventions, template-only skill authoring, and canonical workflow documentation requirements. Its explicit justification for deferring workflow.md changes is appropriate while all proposed behavior remains clearly unimplemented. During execution, resolve the search-index decision without silently authorizing agent-driven rebuilds contrary to current lore, and prevent repository-wide formatting or unrelated test repairs from silently expanding the design-only scope. No blocking lore conflict identified.

### Opened - 2026-10-27T03:40:07Z - John Hoff

Developer approved execution after the independent PASS-WITH-NOTES review.

### Message - 2026-10-27T03:43:01Z - John Hoff

Execution opened with developer approval. Added pending implementation decision proposals and four workflow examples to docs/boss-edition.md. Developer choices requested for branch/skill names, archive restoration and readiness, search freshness and prime projection. No proposal treated as accepted yet. Verification at proposal stage: 810 tests passed; Ruff check passed; Ruff format left all 223 files unchanged; git diff --check passed. Encounter remains open pending design decisions, cross-section reconciliation, and final developer confirmation.

### Message - 2026-10-27T03:48:26Z - John Hoff

Developer accepted merge_target_branch=main and planning_branch=planning, deferring explicit archive restoration because manual reversal is expected to be rare, and the discovery contract (automatic stale-index detection with developer-run rebuild recovery; active boss metadata/summary/budgeted body in prime with explicit broken-link diagnostics). Updated the relevant design sections, verification expectations, and decision record accordingly. Readiness-after-edits and the planning skill name remain pending explicit choices; follow-up question sent. Design whitespace check passes. Previous verification remains 810 tests passing and Ruff clean with 223 files unchanged; only markdown and workflow records changed.

### Message - 2026-10-27T03:50:53Z - John Hoff

Developer accepted the remaining choices: final planning skill name world-planner, and retention of available status after edits with skill-guided readiness reassessment. Updated the lifecycle contract, skill deliverable, accepted decision record, and implementation sequencing in docs/boss-edition.md. Reviewed the complete diff for consistency. All seven original implementation-detail items now have accepted decisions, design examples, or explicit ownership/deferral; no pre-core design blockers remain. Search fingerprint/cache mechanics and prime diagnostic/truncation serialization belong to integration encounters; release/schema decisions belong to release/migration work with early schema assessment if needed. Verification: 810 pytest tests passed; Ruff lint clean; Ruff format left 223 files unchanged; document whitespace check clean. Subsequent changes were markdown only, so runtime checks were not repeated. Design document is ready for final developer confirmation; encounter remains open until that confirmation.

### Completed - 2026-10-27T03:54:32Z - John Hoff

Completed with explicit developer confirmation. Finalized accepted Boss Edition decisions and four workflow examples in docs/boss-edition.md; remaining implementation mechanics and release/schema decisions have named owners. Verification passed: 810 tests, clean Ruff lint, 223 files unchanged by formatting, and clean git diff --check. No runtime implementation or deployed artifacts changed.
