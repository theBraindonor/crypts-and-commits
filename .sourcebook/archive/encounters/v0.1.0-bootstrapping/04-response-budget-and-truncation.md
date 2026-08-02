---
archived: true
campaign: v0.1.0-bootstrapping
created_by: John Hoff
created_on: '2026-07-25T01:22:28Z'
name: 04-response-budget-and-truncation
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-08-02T22:00:20Z'
---

# Response Budget and Truncation

## Requirements

- Enforce a hard 20,000-character budget per response for retrieval outputs (prime, list/map, get).
- Multi-item responses (lists/maps) page under the budget (cursor-based).
- When any response is truncated — including a single body that exceeds the budget — a truncation notice is PREPENDED to the returned content and names the on-disk file path for that content, so it can be read directly as a fallback when the MCP page size is too small to carry it.
- The prepended in-content notice is the primary, mandatory truncation signal (impossible to miss); a structured field may accompany it but does not replace it.

## Rationale

Per `docs/context-management-design.md` (Resolved decision #4 and the progressive-disclosure/budget section). 20,000 characters is the recommended MCP interaction ceiling. Prepending the notice avoids silent client-side truncation — the failure mode from a prior project — because neither side can otherwise detect it. The file-path fallback is a pragmatic escape hatch; it sits in mild tension with the long-term "no awareness of `.sourcebook` layout" goal but is acceptable because direct `Read` of `.sourcebook` is not blocked today and it only fires in the exceptional content-exceeds-budget case.

## Plan

1. `core`: a serialization/budget helper that measures output, pages multi-item responses with a cursor, and, on truncation, prepends the notice + on-disk path.
2. Apply it to the prime/list/get outputs (encounter 03 plus existing list/get).
3. `cli`: surface the cursor / next-page affordance as needed.
4. Tests mirror source: under-budget passthrough, over-budget single body (prepended notice + path), and multi-item paging with a cursor.
5. `clean-tests-and-lint`; preserve `markup=False` for stored content.

## Verification

- `pdm run pytest -q` and `ruff check`/`format` clean, with budget/truncation/paging coverage.
- Manual: a response exceeding 20,000 characters returns with the prepended truncation notice naming the correct on-disk path; a large list pages under the budget.

## Log

### Review - 2026-07-25T02:17:28Z - John Hoff

Reviewed against applicable lore (clean-tests-and-lint, console-best-practices) and the cited docs/context-management-design.md: the Plan correctly implements Resolved Decision #4 (20,000-char budget, cursor-based paging, prepended-notice-plus-on-disk-path as the mandatory signal, structured field optional/non-replacing), honors clean-tests-and-lint via its Verification section, and honors console-best-practices by committing to markup=False for the combined notice+body output since the notice is prepended to stored content rather than sent separately. Two non-blocking notes: Plan step 2's dependency on encounter 03's prime/list/get shape wasn't independently verified (referenced by name, not a cited path), and the optional "structured field" companion to the notice is left unspecified in form. No lore conflicts found; approved to proceed.

### Completed - 2026-07-25T02:37:59Z - John Hoff

Implemented core/budget.py (truncate_body + paginate, budget read from config.RESPONSE_BUDGET=20000 at call time); added public path getters (lore_path/region_path/campaign_path/encounter_path); wired truncate_body into all get commands (lore/region/campaign/encounter/world) plus prime get's world/campaign body sections, and wired paginate + --cursor into all list commands plus prime applicable-lore. Fixed a Rich soft-wrap bug found along the way that was breaking the fallback path across lines. pdm run pytest -q: 465 passed. ruff check/format: clean. Manually verified against a scratch sourcebook: a 25,000-char lore body returns with the notice correctly prepended naming the exact on-disk path; a ~2,000-entry lore list pages correctly with cursor resumption; invalid cursor fails cleanly.
