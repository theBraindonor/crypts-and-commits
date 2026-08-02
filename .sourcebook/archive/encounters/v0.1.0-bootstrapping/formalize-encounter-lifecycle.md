---
archived: true
campaign: v0.1.0-bootstrapping
name: formalize-encounter-lifecycle
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-08-02T22:00:20Z'
---

# Encounter

## Requirements

Retire `cac encounter set-status` entirely and replace it with a firm, code-enforced state
machine plus five purpose-built commands:

- New status set: `draft` -> `reviewed` -> `open` -> `completed`, plus `abandoned` reachable from
  `draft`, `reviewed`, or `open` (not from `completed`, not re-triggerable from `abandoned`).
- Content lock: `encounter update` (whole-body replace) only works while status is `draft`. Once
  status leaves `draft`, `update` is rejected - only appending via the commands below works.
- `encounter review <campaign> <name> --message/-m <text>` - `draft` -> `reviewed`. Message
  required (the lore-review result). This is the point where the four sections become locked.
- `encounter abandon <campaign> <name> --message/-m <text>` - `draft`/`reviewed`/`open` ->
  `abandoned`. Message required.
- `encounter open <campaign> <name> [--message/-m <text>]` - `reviewed` -> `open`. Message
  optional.
- `encounter record-message <campaign> <name> --message/-m <text>` - no status change; valid
  while `reviewed` or `open`. Message required.
- `encounter complete <campaign> <name> [--message/-m <text>]` - `open` -> `completed`. Message
  optional.
- Campaigns are explicitly out of scope: `cac campaign set-status` stays exactly as it is today.

## Rationale

Today, `cac encounter set-status <campaign> <name> <status>` can set an encounter's status to any
of `draft`/`open`/`completed`/`abandoned` from any other status, with no adjacency check - the
"lifecycle" described in the CLI's help text and in `.claude/skills/campaign-manager/SKILL.md`
(lore review before `open`, verification confirmation before `completed`) is purely aspirational
prose that the agent is trusted to follow; nothing in the code enforces it. Likewise, `encounter
update` can replace an encounter's entire body at any time, in any status, so a "reviewed and
approved" plan can silently be rewritten after work has started.

This firms that up at the code layer with a real transition graph and a new `reviewed` status
between `draft` and `open`, and a hard rule that an encounter's four core sections
(Requirements/Rationale/Plan/Verification) can only be replaced wholesale while still in `draft`
- once reviewed, they're locked, and all further detail is appended (never overwritten) via each
command's `--message`.

This repo dogfoods its own framework, so this change also touches the `campaign-manager` skill
(which documents the lifecycle to the agent) and the encounter lifecycle references in CLAUDE.md.

## Plan

1. `core/config.py`: add `"reviewed"` to `ENCOUNTER_STATUSES`.
2. `core/frontmatter_utils.py`: add `append_log_entry(post, *, section, heading, message)` - appends
   a `### <heading>` entry under a running `## Log` section at the end of the body, creating the
   section on first use. No timestamps. Heading text per event: Review, Abandoned, Opened,
   Message, Completed.
3. `core/encounter.py`:
   - Replace `InvalidEncounterStatusError` with `InvalidEncounterTransitionError`,
     `EncounterNotDraftError` (subclass), and `EncounterMessageRequiredError`.
   - Remove `validate_status` and `set_status`.
   - Add `_ENCOUNTER_TRANSITIONS` adjacency map and `_RECORD_MESSAGE_STATUSES`.
   - Add a shared private `_transition(...)` helper used by `review_encounter`, `abandon_encounter`,
     `open_encounter`, `complete_encounter`; add a separate `record_message` function (no status
     change). All return `Encounter`.
   - Add a draft-only guard to `update_encounter`, raising `EncounterNotDraftError` otherwise.
4. `cli/encounter.py`:
   - Remove the `set-status` command.
   - Update the app-level docstring to describe the enforced lifecycle.
   - `update`: check status before opening `$EDITOR`, catch `EncounterNotDraftError`.
   - Add `review`, `abandon`, `open`, `record-message`, `complete` commands with required/optional
     `--message/-m` per the Requirements above, each catching the appropriate core exceptions.
5. Tests: update `tests/core/test_encounter.py`, `tests/core/test_frontmatter_utils.py`, and
   `tests/cli/test_encounter.py` - remove `set_status`/`set-status` tests, add coverage for every
   new function/command and every transition edge case (happy paths, wrong-source-status
   rejections, message-required rejections, missing-encounter rejections, update-blocked-outside-
   draft with body-unchanged assertions, multiple `record-message` calls appending distinct
   ordered `### Message` entries under one `## Log` section).
6. `.claude/skills/campaign-manager/SKILL.md`: replace the `set-status` bullet with the five new
   commands and rewrite the `## Lifecycle` section to describe each real transition and where the
   user-confirmation step belongs.
7. `CLAUDE.md`: update the two encounter lifecycle references to describe the new state machine.

## Verification

- `pdm run pytest -q` - full suite passes, no skips or weakened tests (per `clean-tests-and-lint`).
- `pdm run ruff check .` clean, and `pdm run ruff format .` leaves no diff (per
  `clean-tests-and-lint`).
- Manual smoke test via `pdm run cac`: walk `create` -> `review` -> `open` -> `record-message` ->
  `complete` on a scratch encounter, plus an `abandon` branch from `draft` and from `open`,
  confirming each prints the expected status and that `cac encounter get` shows the accumulating
  `## Log` section; confirm `update` is rejected once past `draft`.

## Log

### Completed

pdm run pytest -q: 276 passed. pdm run ruff check .: clean. pdm run ruff format --check .: clean, 41 files. Manual smoke test in a scratch sourcebook confirmed the full lifecycle (create, update-in-draft, review locks content, record-message while reviewed and while open, open, complete) plus abandon from draft and from open, and rejection of abandon-from-completed and open-from-draft, all producing the expected '## Log' section with ordered '### ...' entries.
