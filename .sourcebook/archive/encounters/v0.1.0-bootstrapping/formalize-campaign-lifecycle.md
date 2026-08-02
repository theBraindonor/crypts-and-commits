---
archived: true
campaign: v0.1.0-bootstrapping
created_by: John Hoff
created_on: '2026-07-24T02:05:05Z'
name: formalize-campaign-lifecycle
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-08-02T22:00:20Z'
---

# Formalize Campaign Lifecycle

## Requirements

1. Replace `cac campaign set-status <name> <status>` with dedicated, code-enforced
   transition commands: `cac campaign open`, `cac campaign pause`, `cac campaign
   complete`, `cac campaign abandon`. Free-form status strings are no longer
   accepted from the CLI.
2. New lifecycle: `draft` -> `open` -> `paused` -> `open` (loop) -> `completed`,
   with `abandoned` reachable from `draft`, `open`, or `paused` (not from
   `completed`). Concretely:
   - `draft` -> `open` or `abandoned`
   - `open` -> `paused`, `completed`, or `abandoned`
   - `paused` -> `open`, `completed`, or `abandoned`
   - `completed`, `abandoned` -> terminal (no further transitions)
3. Only one campaign may be `open` at a time. Attempting to open a second
   campaign while another is already `open` must fail with a clear error naming
   the campaign that is blocking it.
4. A campaign cannot move to `paused`, `completed`, or `abandoned` while it has
   any encounter in `open` status. The error must name the blocking encounter(s).
5. Campaigns gain `created_on`, `created_by`, `updated_on`, and `updated_by`
   frontmatter attributes, stamped the same way encounters already do (see
   `_stamp_created`/`_stamp_updated` in `cac/core/encounter.py`): `created_*` set
   once on `create`, `updated_*` refreshed on every subsequent write (`update`
   and every status transition).
6. `cac campaign list` must also show each campaign's current status, not
   just its name.

## Rationale

`cac campaign set-status` currently accepts any of the four `CAMPAIGN_STATUSES`
with no guard rails, so nothing stops two campaigns from being open
simultaneously or a campaign being paused/completed/abandoned out from under
in-flight work. Encounters already went through this exact hardening
(`formalize-encounter-lifecycle`): a fixed transition map, dedicated commands,
and `created_on`/`created_by`/`updated_on`/`updated_by` stamps via
`git_utils.current_git_user`. This encounter brings campaigns to the same
standard and adds two campaign-specific invariants (single open campaign,
no pausing/completing/abandoning past open encounters) that encounters don't
need because they don't nest other lifecycle objects.

The open-encounter guard needs to read encounter statuses from `campaign.py`,
but `encounter.py` already imports `campaign.py` (for `campaign_core.exists`/
`validate_name`) — importing `encounter.py` back from `campaign.py` would
create a circular dependency between the two core modules. `campaign.py` will
instead scan its own encounters directory directly via `frontmatter.load`
(using `ENCOUNTER_DIR_NAME`/`DEFAULT_ENCOUNTER_STATUS` from `config.py`, the
same constants `encounter.py` uses), matching the existing one-directional
dependency (encounter -> campaign, not the reverse).

The `created_*`/`updated_*` stamping helpers will be duplicated locally in
`campaign.py` rather than extracted into a shared helper in
`frontmatter_utils.py`. `encounter.py` already keeps these as private,
module-local helpers rather than shared ones, so mirroring that (rather than
introducing a new shared abstraction as part of this change) keeps the diff
consistent with the existing pattern.

## Plan

1. **`cac/core/config.py`** — extend `CAMPAIGN_STATUSES` to
   `("draft", "open", "paused", "completed", "abandoned")`.
2. **`cac/core/campaign.py`**:
   - Remove `validate_status`, `InvalidCampaignStatusError`, and `set_status`
     (no longer reachable from the CLI).
   - Add `CREATED_BY_KEY`/`CREATED_ON_KEY`/`UPDATED_BY_KEY`/`UPDATED_ON_KEY`
     constants and private `_stamp_created(post, root)` /
     `_stamp_updated(post, root)` helpers, mirroring `encounter.py` exactly
     (using `git_utils.current_git_user` and
     `frontmatter_utils.format_timestamp(frontmatter_utils.utcnow())`).
   - Add a `_CAMPAIGN_TRANSITIONS` map matching Requirement 2.
   - Add exceptions: `InvalidCampaignTransitionError(ValueError)`,
     `AnotherCampaignOpenError(ValueError)`,
     `CampaignHasOpenEncountersError(ValueError)`.
   - Add `open_campaign(root, name) -> Campaign`, `pause_campaign(root, name)`,
     `complete_campaign(root, name)`, `abandon_campaign(root, name)`, each:
     validating the transition against `_CAMPAIGN_TRANSITIONS` (raising
     `InvalidCampaignTransitionError` listing the allowed next states, same
     style as `encounter._transition`), applying the relevant guard, stamping
     `updated_by`/`updated_on`, and writing the new status.
   - Add `_other_open_campaign(root, exclude) -> str | None` (scans
     `list_campaigns` via `frontmatter.load`, returns the first other
     campaign whose status is `open`) used by `open_campaign`.
   - Add `_open_encounter_names(root, name) -> list[str]` (scans
     `sourcebook_dir(root) / ENCOUNTER_DIR_NAME / name / *.md` directly via
     `frontmatter.load`, no import of `encounter.py`) used by `pause_campaign`,
     `complete_campaign`, and `abandon_campaign`.
   - Update `create_campaign` to call `_stamp_created`; update
     `update_campaign` to call `_stamp_updated`.
   - Add `list_campaigns_with_status(root) -> list[tuple[str, str]]`
     alongside `list_campaigns` (reads each campaign's status via
     `frontmatter.load`, same directory scan as `list_campaigns`).
3. **`cac/cli/campaign.py`**:
   - Remove the `set-status` command.
   - Add `open`, `pause`, `complete`, `abandon` commands (no `--message`
     option — campaigns don't carry a message log the way encounters do),
     each catching `CampaignNotFoundError`, `InvalidCampaignTransitionError`,
     and `GitIdentityError`; `open` additionally catches
     `AnotherCampaignOpenError`; `pause`/`complete`/`abandon` additionally
     catch `CampaignHasOpenEncountersError`.
   - Add `GitIdentityError` to the existing `create`/`update` commands' catch
     blocks (they now stamp git identity too).
   - Change the `list` command to use `list_campaigns_with_status` and print
     `f"{name} ({status})"` per line instead of bare names.
   - Update the module's Typer `help=` text to describe the new lifecycle
     instead of the old draft/open/completed/abandoned + set-status wording.
4. **Tests**:
   - `tests/core/test_campaign.py`: drop the `set_status` tests; add coverage
     for each new transition function's happy path, its invalid-transition
     rejection, the single-open-campaign conflict (and its error message
     naming the other campaign), the open-encounter guard blocking
     pause/complete/abandon (and its error message naming the encounter), and
     that `create_campaign`/`update_campaign`/each transition stamp
     `created_by`/`created_on`/`updated_by`/`updated_on` correctly — following
     the existing `_set_identity`/`_default_identity` monkeypatch pattern
     already used in `tests/core/test_encounter.py`.
   - `tests/cli/test_campaign.py`: drop the `set-status` tests; add CLI-level
     tests for `open`/`pause`/`complete`/`abandon` (success, not-found,
     invalid transition, the two guard failures, and git-identity failure —
     mirroring `tests/cli/test_encounter.py`'s `_break_git_identity` pattern),
     plus a test that `list` shows each campaign's status alongside its name.
5. **`.claude/skills/campaign-manager/SKILL.md`** — update the Campaigns
   section: replace the `set-status` bullet with `open`/`pause`/`complete`/
   `abandon`, and add a short lifecycle description (mirroring the existing
   `## Lifecycle` section's style for encounters) covering: `draft` is the
   creation state; only one campaign may be `open` at a time; `paused` is only
   reachable from `open`; `pause`/`complete`/`abandon` all require no open
   encounters under that campaign first.

## Verification

- `pdm run pytest -q` passes with no skipped or weakened tests, including all
  new/updated campaign and encounter tests.
- `pdm run ruff check .` is clean and `pdm run ruff format .` leaves no diff.
- Manual smoke test via `pdm run cac`:
  1. `cac campaign create test-a` (status `draft`) — confirm
     `created_on`/`created_by`/`updated_on`/`updated_by` appear via
     `cac campaign get test-a`.
  2. `cac campaign open test-a` succeeds; `cac campaign create test-b` then
     `cac campaign open test-b` fails with a clear "already open" error naming
     `test-a`.
  3. `cac encounter create test-a some-encounter`, review/open it, then
     `cac campaign pause test-a` fails with a clear error naming
     `some-encounter`; `cac encounter complete test-a some-encounter` (after
     `review`/`open`) then `cac campaign pause test-a` succeeds.
  4. `cac campaign open test-a` (re-open from `paused`) succeeds;
     `cac campaign complete test-a` succeeds.
  5. `cac campaign list` shows `test-a`'s status alongside its name.
  6. `cac campaign set-status ...` no longer exists (`cac campaign --help`
     confirms).

## Log

### Review - 2026-07-24T02:08:50Z - John Hoff

Lore check passed: clean-tests-and-lint (world) satisfied by Verification's pytest/ruff gate; console-best-practices (crypts-and-commits region) satisfied since campaign list will only print name/status, both pattern/enum-constrained and unable to carry bracket markup, consistent with the existing get_campaign metadata-printing precedent. Plan approved by user as drafted.

### Opened - 2026-07-24T02:09:08Z - John Hoff

Starting implementation per the reviewed plan.

### Message - 2026-07-24T02:15:30Z - John Hoff

Verification deviation: rather than creating throwaway test-a/test-b campaigns as originally written, ran the manual smoke test against this repo's real live sourcebook data instead (v0.1.0-bootstrapping is already open with this very encounter open under it), since that avoided polluting production .sourcebook state and gave an equally strong (arguably stronger) real-world check: confirmed 'cac campaign --help' lists open/pause/complete/abandon and no longer lists set-status; 'cac campaign list' shows 'v0.1.0-bootstrapping (open)'; 'cac campaign open v0.1.0-bootstrapping' (already open) correctly fails with the invalid-transition message; 'cac campaign pause v0.1.0-bootstrapping' correctly fails naming 'formalize-campaign-lifecycle' as the blocking open encounter. Full automated coverage of the single-open-campaign conflict and all transition/guard combinations lives in the new pytest suite (74 new tests across core/CLI), which all pass alongside the full existing suite (326 total), and ruff check/format are both clean.

### Completed - 2026-07-24T02:16:25Z - John Hoff

Implemented and verified: campaign lifecycle commands (open/pause/complete/abandon), single-open-campaign guard, open-encounter guard, created/updated stamping, and campaign list status display. 74 new tests added, full suite (326) passes, ruff clean. Skill doc updated.
