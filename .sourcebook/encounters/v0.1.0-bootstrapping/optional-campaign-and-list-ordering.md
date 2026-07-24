---
campaign: v0.1.0-bootstrapping
created_by: John Hoff
created_on: '2026-07-24T04:30:02Z'
name: optional-campaign-and-list-ordering
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-07-24T04:42:31Z'
---

# Optional Campaign and Encounter List Ordering

## Requirements

1. **`cac encounter list` orders by date.** Encounters are listed in ascending
   order by their `updated_on` frontmatter timestamp (oldest first). An
   encounter missing `updated_on` is treated as EPOCH and therefore sorts
   first; ties (including among attribute-less encounters) may order
   arbitrarily — that non-determinism is acceptable.
2. **The campaign becomes optional on the encounter commands.** It is no longer
   a required positional argument; it becomes an optional `--campaign`/`-c`
   option that defaults to the currently active (open) campaign.
   - When `--campaign` is omitted and no campaign is `open`, the command fails
     with a clear message telling the user to pass `--campaign`.
   - For **mutating** commands (`create`, `update`, `delete`, `review`, `open`,
     `complete`, `abandon`, `record-message`, `assign-region`,
     `unassign-region`), an explicitly named `--campaign` must not be
     `completed` or `abandoned`. The default/active campaign is always `open`,
     so it always qualifies.
   - **Read** commands (`get`, `list`) may target any existing campaign
     regardless of status, so history under a `completed`/`abandoned` campaign
     stays inspectable.
   - The `list` command gains the same `--campaign`/`-c` option.
3. **The `campaign-manager` skill is updated** so the agent knows the new
   invocation form: campaign optional and defaulting to the active campaign,
   the `--campaign` flag for other (non-completed/non-abandoned) campaigns, and
   the new list ordering.

## Rationale

Requiring the campaign name on every encounter command is redundant during
normal work, when exactly one campaign is open and nearly all encounter
activity happens inside it. Defaulting to the active campaign removes that
friction, while `--campaign` preserves the ability to reach into another
in-progress campaign. Refusing to mutate `completed`/`abandoned` campaigns keeps
closed history immutable, consistent with the encounter lifecycle's own
terminal states, while still allowing `get`/`list` to read that history.
Ordering `list` ascending by `updated_on` places stale items first and
recently-touched work last, and the EPOCH fallback keeps any legacy encounter
without the attribute from being hidden.

## Plan

### Core — `core/campaign.py`
- Add `active_campaign(root) -> str | None`, returning the single `open`
  campaign's name (or `None`), built on `list_campaigns_with_status`. Refactor
  `_other_open_campaign` to reuse it where convenient.
- Add `NoActiveCampaignError` and `CampaignNotMutableError` (ValueError
  subclasses).
- Add `resolve_campaign(root, campaign: str | None, *, require_mutable: bool) -> str`:
  - `campaign is None` → return `active_campaign(root)`; raise
    `NoActiveCampaignError` if none is open.
  - otherwise → raise `CampaignNotFoundError` if it does not exist; if
    `require_mutable` and its status is `completed`/`abandoned`, raise
    `CampaignNotMutableError`.

### Core — `core/encounter.py`
- Change `list_encounters` to sort by `updated_on` ascending with an
  EPOCH/empty fallback: load each file's frontmatter and key on
  `post.get("updated_on", "")`. The fixed-width `%Y-%m-%dT%H:%M:%SZ` format
  sorts chronologically as text, and an empty/missing value sorts first.

### CLI — `cli/encounter.py`
- Replace the `campaign` positional `typer.Argument` with
  `campaign: str | None = typer.Option(None, "--campaign", "-c", ...)` on every
  command; keep `name` positional.
- At the start of each command, resolve the campaign via
  `campaign_core.resolve_campaign(Path.cwd(), campaign, require_mutable=<True for
  mutating commands, False for get/list>)`, catching `NoActiveCampaignError`,
  `CampaignNotFoundError`, and `CampaignNotMutableError` through `fail`.
- No new stored-body prints are introduced, so the `console-best-practices`
  `markup=False` rule is already satisfied by the existing `get` command.

### Skill — `.claude/skills/campaign-manager/SKILL.md`
- Update every `cac encounter ...` usage line and lifecycle description to the
  new form: campaign optional / `--campaign`, default-to-active behavior, the
  completed/abandoned mutation restriction, and list ordered ascending by
  `updated_on`.

### Tests
- Update `tests/cli/test_encounter.py` invocations to the new option form; add
  cases for default-to-active, `--campaign` targeting, the no-active-campaign
  error, and the completed/abandoned mutation block.
- Add a `tests/core/test_encounter.py` ordering test (updated_on ascending,
  missing → first).
- Add `tests/core/test_campaign.py` tests for `active_campaign` and
  `resolve_campaign` (both branches, mutable guard).

## Verification

- `pdm run pytest -q` passes with no skips added to dodge failures.
- `pdm run ruff check .` reports zero errors and `pdm run ruff format .` leaves
  no diffs.
- Manual smoke: `pdm run cac encounter list` (no campaign) lists the active
  campaign's encounters oldest-first; `pdm run cac encounter get <name>` works
  without a campaign; `--campaign <completed-campaign>` is rejected for `create`
  but allowed for `get`/`list`; omitting `--campaign` with no open campaign
  fails with a clear message.

## Log

### Review - 2026-07-24T04:32:11Z - John Hoff

Lore review passed. World lore clean-tests-and-lint is satisfied by the Verification section (pytest + ruff check/format, no skip/noqa dodges). Region lore console-best-practices (crypts-and-commits) is not implicated: the refactor adds no new prints of stored .sourcebook body text; the only such print (encounter 'get') already uses markup=False. User approved the flagged CLI-surface change (campaign positional -> --campaign/-c option, breaking change requiring test rewrites).

### Completed - 2026-07-24T04:42:31Z - John Hoff

Implemented and verified. list_encounters sorts ascending by updated_on (missing -> first); campaign is now an optional --campaign/-c option across all encounter commands, defaulting to the active (open) campaign, with mutating commands refusing completed/abandoned campaigns and get/list allowing any. campaign-manager skill updated. Full suite 348 passed; ruff check + format --check clean; manual smoke of list/get default resolution and missing-campaign error all pass.
