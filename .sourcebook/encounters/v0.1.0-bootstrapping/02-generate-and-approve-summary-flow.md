---
campaign: v0.1.0-bootstrapping
created_by: John Hoff
created_on: '2026-07-25T01:22:25Z'
name: 02-generate-and-approve-summary-flow
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-07-25T02:02:07Z'
---

# Generate-and-Approve Summary Flow

## Requirements

- When a region's or lore's body is created or edited, a current summary is
(re)generated and the GM approves it as part of the same change — the
generate-and-approve model.
- The summary must never be stale relative to the body: the summary write is
wired into the same core transition that writes the body (and stamps
`updated_on`), so a body change cannot commit without an accompanying
within-cap summary. This is a structural guarantee, not a convention — no core
path writes a body without also writing a summary.
- Respect the 500-character cap established in encounter 01 (reuse its
enforcement; the cap applies on the body-write path, not only the standalone
setter).
- The drafting mechanism (see Rationale) is chosen and documented as part of
this encounter.

## Rationale

Per `docs/context-management-design.md` (Resolved decision #1). Summaries are a
governance-adjacent artifact — lore summaries route the review gate — so a
human approval gate is retained rather than silent auto-generation. Tying
regeneration to the write transition is what makes the "never stale" guarantee
real, using the same write-path ownership CAC already relies on for
`updated_on` stamping. This builds the workflow on top of the storage
established in encounter 01.

Resolution of the drafting sub-decision — **caller-supplied draft, GM-approved
(candidate (a))**. Today's CLI has no in-process LLM, so "the tool drafts" is
realized as: the calling agent proposes the summary and passes it into the same
command that writes the body; the GM approves it while overseeing the session
(the proposed summary is visible in the agent's command before it runs). The
tool's enforceable job this encounter is narrow and deterministic: a body write
cannot commit without an accompanying within-cap summary. Deterministic
extraction (candidate (b)) is rejected — leading body text is usually a
markdown heading, a weak routing signal — and a blocking editor pre-fill
(candidate (c)) is rejected because it hangs when the agent drives `cac`
non-interactively, which is the primary flow. True model-generated drafting
arrives with the MCP/agent surface (encounter 06); formalizing an explicit
propose/approve prompt in the skills is deferred to encounter 05. Approval is
therefore a session/skill concern for now, while the never-stale + cap
invariant is enforced in code here.

## Plan

1. `core/lore.py`, `core/region.py`: make `summary` a required companion of the
body-writing transitions. `create_lore(root, name, body, summary)` and
`update_lore(root, name, body, summary)` (and `create_region(root, name, body,
summary, path_value="")` / `update_region(root, name, body, summary)`) write
body and summary together in a single `write_post`, enforcing the cap via the
existing `set_summary_attribute` (raising `SummaryTooLongError`). No body-write
path remains that omits a summary. The standalone `set_summary` (encounter 01)
stays — a summary-only update cannot create staleness.
2. `cli/lore.py`, `cli/region.py`: add a `--summary`/`-s` option to `create` and
`update`; the caller (agent) supplies the proposed summary alongside `--body`.
A body write with no summary fails via `fail(...)` with an actionable message
rather than silently committing a stale/absent summary. On the `SummaryTooLongError`
path, surface the cap error the same way. Any place that echoes the stored
summary back to the user prints it with `markup=False` per `console-best-practices`;
CLI-authored confirmations (e.g. `Updated <path>`) may keep markup.
3. Update every existing caller and test of the changed core signatures
(`create_lore`/`update_lore`/`create_region`/`update_region`) to pass a summary —
this is a deliberate breaking signature change that makes the invariant
structural.
4. Tests mirror source (`tests/core/test_lore.py`, `test_region.py`, and the
matching `cli` tests): regeneration-on-edit (an `update` writes the new
summary), the never-stale invariant (a body write with no summary is rejected
at the CLI; no core path writes a body without a summary), cap enforcement on
the write path, and round-trip — on both region and lore.
5. `clean-tests-and-lint`.

## Verification

- `pdm run pytest -q` and `ruff check`/`format` clean, with coverage for
regeneration-on-edit, the never-stale rejection, cap-on-write, and round-trip.
- Editing a region/lore body with `cac ... update --body ... --summary ...`
stores the new summary alongside the new body; the stored summary reflects the
new body. Attempting a body write without a summary is rejected.
- The 500-char cap and placeholder behavior from encounter 01 still hold
(over-cap summary rejected on the write path; absent summary still returns the
placeholder on read).

## Log

### Review - 2026-07-25T01:51:17Z - John Hoff

Reviewed against applicable lore: clean-tests-and-lint (world) and console-best-practices (region crypts-and-commits). Both honored: Plan step 2 correctly commits to markup=False for any echoed stored summary while allowing markup on CLI-authored confirmations, matching the source-of-text rule; steps 4-5 and Verification add source-mirrored tests and require clean pytest + ruff without weakening checks. Plan's factual claims verified against core/cli lore.py and region.py - set_summary_attribute, SummaryTooLongError, the four target signatures, and encounter 01's standalone set_summary all exist as described. PASS-WITH-NOTES. Non-lore flags: 'update every existing caller' (step 3) is not enumerated - main thread confirmed the only callers are cli/lore.py, cli/region.py, and test setup in test_lore.py, test_region.py, test_encounter.py, test_world.py (bootstrap.py does not call them); and the 500-char cap value and design decision are cited to docs/context-management-design.md and encounter 01, both since read and confirmed.

### Message - 2026-07-25T02:01:02Z - John Hoff

Implementation note on Plan step 3 (the reviewer's flagged 'callers not enumerated' risk): beyond cli/lore.py, cli/region.py and the core test files, the required-summary signature change also reached CLI-invocation setup in tests/cli/test_encounter.py (region create/update driven through the CLI, not the core functions) and setup calls in tests/core/test_world.py and tests/core/test_encounter.py. All were updated. bootstrap.py does not call the changed functions. No production caller beyond the two CLI modules.

### Completed - 2026-07-25T02:02:07Z - John Hoff

Implemented generate-and-approve summary flow (caller-supplied, GM-approved). Made summary a required companion of the body-writing core transitions (create_lore/update_lore, create_region/update_region write body+summary in one write, cap enforced via set_summary_attribute, over-cap aborts before any write); added --summary/-s to the create/update CLI commands with an actionable failure when a body write carries no summary; standalone set_summary retained. Mirrored tests cover round-trip, regeneration-on-edit, never-stale rejection (core+CLI), cap-on-write, and rejected-update atomicity. Verification green: 402 tests pass, ruff check/format clean, and a real-CLI smoke test confirms a summary-less body write is rejected without creating anything. Explicit approval prompt deferred to the skills (enc 05); model-generated drafting deferred to the MCP/agent surface (enc 06).
