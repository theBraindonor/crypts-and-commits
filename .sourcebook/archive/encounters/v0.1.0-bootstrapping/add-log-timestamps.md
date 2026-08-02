---
archived: true
campaign: v0.1.0-bootstrapping
name: add-log-timestamps
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-08-02T22:00:20Z'
---

# Requirements

Encounters need a record of *who* touched them and *when*, at two levels:

1. **Log entries.** Every `### <heading>` line `append_log_entry` writes into an encounter's
   `## Log` section gains a timestamp and the git user who caused it, e.g.
   `### Review - 2026-07-23T18:04:12Z - John Hoff` (UTC, second precision, ISO 8601 with a
   literal `Z` offset; identity is `git config user.name` only, no email).
2. **Frontmatter fields.** Every encounter gains four new frontmatter keys:
   - `created_by` / `created_on` - set once, at `create`, and never changed again.
   - `updated_by` / `updated_on` - set at `create` (equal to the created values) and
     refreshed on every subsequent touch: `update`, `review`, `abandon`, `open`,
     `record-message`, `complete`, `assign-region`, `unassign-region`.

No new required CLI parameters anywhere - both the timestamp and the git identity are captured
automatically, the same way a git commit captures author/date without either being typed in.

If the current git user's name can't be resolved (git not installed, or `user.name` unset
locally and globally), the operation must fail with a clear, actionable error instead of
proceeding with a placeholder value.

Scope is deliberately limited to encounters (matching how they're already the only object type
with a `## Log` section); extending `created_by`/`created_on`/`updated_by`/`updated_on` to
world/lore/region/campaign is a reasonable future idea but out of scope here.

# Rationale

The prior draft of this encounter added timestamps to Log entries alone. Timestamps answer
"when," but a shared-repo, multi-session workflow like this one also needs "who" - an encounter
might get drafted by one person, reviewed by another, and reopened by a third weeks later, and
right now nothing in the file records that. Piggybacking on `git config user.name` costs nothing
extra to set up (anyone committing to this repo already has it configured) and matches the
attribution model developers already trust from `git blame`/`git log`.

Failing hard when identity can't be resolved (rather than falling back to a placeholder) was a
deliberate choice: a silently wrong "unknown" author is worse than a blocked command with a
one-line fix (`git config user.name "..."`).

# Plan

1. `core/frontmatter_utils.py`:
   - Add `from datetime import datetime, timezone`.
   - Add `utcnow() -> datetime` (thin wrapper over `datetime.now(timezone.utc)`) and
     `format_timestamp(ts: datetime) -> str` (`%Y-%m-%dT%H:%M:%SZ`), both public so
     `core/encounter.py` can reuse the same clock for frontmatter stamps, not just Log entries.
   - `append_log_entry` gains a `user: str` keyword-only parameter; the entry line becomes
     `f"### {heading} - {format_timestamp(utcnow())} - {user}"`.
2. New `core/git_utils.py`:
   - `class GitIdentityError(RuntimeError)`.
   - `current_git_user(root: Path) -> str` - runs `git config user.name` with `cwd=root`
     (this naturally resolves local-then-global-then-system, same as git itself); raises
     `GitIdentityError` on `FileNotFoundError` (git missing) or a non-zero exit / blank stdout
     (identity unset), with a message telling the user how to fix it
     (`git config user.name "Your Name"`).
3. `core/encounter.py`:
   - Add `CREATED_BY_KEY`, `CREATED_ON_KEY`, `UPDATED_BY_KEY`, `UPDATED_ON_KEY` constants
     (string literals), alongside the existing `REGIONS_KEY` pattern.
   - Add `_stamp_created(post, root)` - resolves the git user once, sets all four keys to the
     same user/timestamp.
   - Add `_stamp_updated(post, root)` - sets only `updated_by`/`updated_on`.
   - `create_encounter`: call `_stamp_created` before `write_post`.
   - `update_encounter`, `_transition` (covers `review`/`abandon`/`open`/`complete`),
     `record_message`, `_update_regions` (covers `assign_region`/`unassign_region`): call
     `_stamp_updated` before `write_post`. Every call site that appends a log entry now passes
     `user=` through to `append_log_entry` using the same resolved identity used for the stamp,
     so one `current_git_user` call per operation serves both the Log line and the frontmatter
     update.
4. `cli/encounter.py`: every command that can now raise `GitIdentityError`
   (`create`, `update`, `review`, `abandon`, `open`, `complete`, `record-message`,
   `assign-region`, `unassign-region`) catches it alongside its existing exceptions and calls
   `fail(console, str(exc))`. `get`/`list`/`delete` are unaffected (delete doesn't touch content).
5. Tests:
   - New `tests/core/test_git_utils.py`: monkeypatch `subprocess.run` to cover the success case,
     `FileNotFoundError`, non-zero exit, and blank-stdout cases, each asserting
     `GitIdentityError` where expected.
   - `tests/core/test_frontmatter_utils.py`: monkeypatch `utcnow` for deterministic output;
     update `append_log_entry` tests for the new `user` parameter and the extended entry format;
     keep one regex-based test against the real (non-monkeypatched) `utcnow`/`format_timestamp`.
   - `tests/core/test_encounter.py`: monkeypatch `git_utils.current_git_user` (fixed name) and
     `frontmatter_utils.utcnow` (fixed time) throughout. Add coverage for:
     - `create_encounter` sets all four keys identically.
     - A subsequent `update`/`review`/`open`/etc. changes `updated_by`/`updated_on` but leaves
       `created_by`/`created_on` untouched (use two distinct monkeypatched users/times across
       the two calls to prove this, not just re-assert the same value).
     - Each mutating function propagates `GitIdentityError` when `current_git_user` raises it,
       and that the file on disk is left unchanged in that case.
   - `tests/cli/test_encounter.py`: for at least `create` and one status-transition command,
     monkeypatch `current_git_user` to raise and assert a non-zero exit with the error message
     surfaced.

# Verification

- `pdm run pytest -q` - full suite passes (per `clean-tests-and-lint`).
- `pdm run ruff check .` clean, `pdm run ruff format .` leaves no diff (per
  `clean-tests-and-lint`).
- Manual smoke test via `pdm run cac`: run `create` -> `review` -> `open` -> `record-message` ->
  `complete` on a scratch encounter and confirm `cac encounter get` shows `created_by`/
  `created_on` fixed from the first step, `updated_by`/`updated_on` advancing each step, and
  every `## Log` entry carrying both a timestamp and the git user. Then temporarily unset
  `user.name` (`git config --unset user.name` in a scratch repo, or run outside any repo with no
  global identity set) and confirm a mutating command fails with a clear error rather than
  writing a placeholder.

## Log

### Review

Checked against console-best-practices (region: crypts-and-commits) and clean-tests-and-lint (world). No new console.print of stored content is introduced - the new GitIdentityError messages are CLI/core-authored strings routed through the existing fail() helper, same as every other caught exception in cli/encounter.py, so no markup=False concern. The pre-existing 'cac encounter get' metadata loop prints all frontmatter values (including the new created_by/created_on/updated_by/updated_on) without markup=False, but that's an existing pattern already applied to name/campaign/status/regions, not something this Plan introduces or changes - left out of scope. Verification section already requires pdm run pytest -q and ruff check/format clean, satisfying clean-tests-and-lint.

### Message - 2026-07-24T01:50:02Z - John Hoff

Implemented: core/frontmatter_utils.py (utcnow/format_timestamp, append_log_entry now takes user=), new core/git_utils.py (current_git_user/GitIdentityError via 'git config user.name'), core/encounter.py (created_by/created_on/updated_by/updated_on stamped via _stamp_created/_stamp_updated at every mutating call site), cli/encounter.py (GitIdentityError caught in all mutating commands). pdm run pytest -q: 291 passed. ruff check/format: clean. Manual smoke test in a scratch git repo confirmed created_on/created_by fixed across review->open->record-message->complete while updated_on/updated_by advanced each step, every Log entry carries a timestamp and git user, and unsetting git identity (local+global) makes a mutating command fail with a clear error and leaves the file byte-for-byte unchanged.

### Completed - 2026-07-24T01:50:24Z - John Hoff

Closed: log entries and encounter frontmatter now carry timestamps and git-user attribution. Full lifecycle smoke-tested; pytest and ruff clean.
