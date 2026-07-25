---
campaign: v0.1.0-bootstrapping
created_by: John Hoff
created_on: '2026-07-25T14:13:23Z'
depends_on: []
name: campaign-postmortem-on-terminal
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-07-25T14:32:49Z'
---

# Campaign Postmortem On Terminal

## Requirements

- `cac campaign complete <name> --message/-m "..."` requires a non-blank message (the postmortem); reject with a clear, actionable error if the option is omitted or blank, mirroring how encounter transitions already reject a missing required message.
- `cac campaign abandon <name> --message/-m "..."` requires a non-blank message (the postmortem) under the same rule.
- `cac campaign pause <name>` and `cac campaign open <name>` are unchanged — no message required, since neither moves a campaign to a terminal status.
- The postmortem message is appended to the campaign body as a dated, attributed log entry (heading `Completed` or `Abandoned`, timestamp, git user) under a running `## Log` section created on first use — reusing `frontmatter_utils.append_log_entry`, the exact mechanism encounter transitions already use.
- Once a campaign's status is `completed` or `abandoned` (terminal), `cac campaign update <name>` must fail with a clear error instead of replacing the body — a campaign's record is closed once its postmortem is written, so nothing can rewrite the story that postmortem documents.
- `cac campaign delete <name>` is unaffected by this change — deletion remains available regardless of status; that is not in scope here.
- The existing terminal-status guardrail already used to block encounter creation/mutation under a completed/abandoned campaign (`CampaignNotMutableError`, raised from `resolve_campaign`) keeps its current behavior unchanged; body-edit blocking reuses that same exception type with body-specific wording, not a new mechanism.

## Rationale

The current lifecycle lets a campaign reach `completed` or `abandoned` with no required narrative captured anywhere — nothing records whether the initiative succeeded, what was learned, or why it was abandoned. Encounters already enforce this kind of accountability at their own gates (`review` and `abandon` both require `--message`); campaigns have no equivalent today, which is inconsistent with this project's own purpose of being a durable record rather than an ephemeral one. Locking the body once a campaign is terminal turns `completed`/`abandoned` into an actual closed record instead of just a status label — without that lock, the story a postmortem is meant to preserve could still be rewritten out from under it after the fact. Reusing `frontmatter_utils.append_log_entry` (already relied on by encounter transitions) keeps campaigns and encounters structurally consistent rather than introducing a second logging convention for the same idea.

## Plan

1. In `packages/crypts-and-commits/src/cac/core/campaign.py`: add a `CampaignMessageRequiredError(ValueError)` exception, mirroring `encounter.EncounterMessageRequiredError`. Refactor `_guarded_transition` to accept a `log_heading: str | None` and `message: str | None`; when `to_status` is `completed` or `abandoned`, require and validate a non-blank message (raising `CampaignMessageRequiredError` otherwise) and append it via `frontmatter_utils.append_log_entry(post, section="Log", heading=log_heading, message=message, user=user)` before the status write, mirroring encounter's `_transition`. Update `complete_campaign`/`abandon_campaign` to accept a required `message: str`; leave `pause_campaign` message-less.
2. In the same module, update `update_campaign` to check `_TERMINAL_STATUSES` before replacing `post.content`, raising `CampaignNotMutableError` (reusing the existing exception type, with wording specific to body edits, distinct from its existing encounter-mutation-blocking message) when the campaign is `completed` or `abandoned`.
3. In `packages/crypts-and-commits/src/cac/cli/campaign.py`: add a required `--message`/`-m` option to the `complete` and `abandon` commands (matching the encounter CLI's `review`/`abandon` pattern), thread it to core, and catch `CampaignMessageRequiredError`. Catch `CampaignNotMutableError` in the `update` command and route it through `fail()`.
4. Update the `cac campaign` Typer app's top-level help text and the `complete`/`abandon`/`update` command docstrings to describe the postmortem requirement and terminal immutability, matching the encounter app's existing help-text conventions.
5. Extend `packages/crypts-and-commits/tests/core/test_campaign.py` and `packages/crypts-and-commits/tests/cli/test_campaign.py`: missing/blank-message rejection for `complete` and `abandon`; log-entry section/heading/content/attribution verification; `update` rejection once `completed` or once `abandoned`; confirm `pause`/`open` remain message-less and unaffected; confirm existing encounter-mutation-blocking behavior under a terminal campaign is unchanged.
6. Update both `.claude/skills/campaign-manager/SKILL.md` and `.agents/skills/campaign-manager/SKILL.md`: document the required `--message` on `complete`/`abandon` as the postmortem, and note `update` now fails once a campaign is `completed`/`abandoned`.
7. Review `CLAUDE.md`'s campaign/domain-model description during implementation and update it if it describes campaign mutability or the complete/abandon commands in a way this change would make inaccurate.

## Verification

- Run `pdm run pytest packages/crypts-and-commits/tests/core/test_campaign.py packages/crypts-and-commits/tests/cli/test_campaign.py -q` for focused coverage, then `pdm run pytest -q` for the full suite.
- Run `pdm run ruff check .` and `pdm run ruff format .`.
- Do not exercise the new commands against this repository's own live `.sourcebook` / active campaign (`v0.1.0-bootstrapping`) as ad hoc manual testing — verification relies on the test suite's isolated fixtures only. Actually completing `v0.1.0-bootstrapping` under the new postmortem requirement is a separate, later action, not part of this encounter's verification.

## Log

### Review - 2026-07-25T14:22:24Z - John Hoff

Verified against both applicable lore items via cac prime applicable-lore (clean-tests-and-lint, console-best-practices). clean-tests-and-lint is satisfied: Verification runs the focused test files, then the full pytest suite, then ruff check/format, matching the lore's gate exactly. console-best-practices is satisfied: the postmortem message reaches users only via the existing cac campaign get body print, which already uses markup=False (cli/campaign.py:42, unchanged by this plan); the new CampaignMessageRequiredError/CampaignNotMutableError error paths follow the pre-existing fail()-with-markup convention already used identically for every other campaign transition error, so this introduces no new risk. Cross-checked the plan's claimed reuse of frontmatter_utils.append_log_entry and encounter.py's _transition message_required/log_heading pattern against the actual source (encounter.py:290-317, frontmatter_utils.py:57) and confirmed both exist exactly as described - the plan is not mirroring a mechanism that doesn't hold up. No conflicts found; approved to proceed to reviewed.

### Completed - 2026-07-25T14:32:49Z - John Hoff

Implemented: complete/abandon now require a postmortem --message, logged via frontmatter_utils.append_log_entry; update rejects terminal campaigns. Verification passed: focused + full pytest suite (504 passed), ruff check clean, ruff format clean.
