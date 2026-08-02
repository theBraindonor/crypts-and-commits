---
archived: true
campaign: v0.1.2-encounter-indexing-and-search
created_by: John Hoff
created_on: '2026-07-27T03:31:43Z'
depends_on: []
name: add-created-updated-stamps-to-world-lore-region
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-08-02T22:13:48Z'
---

## Requirements

- `world.md`, every `lore/<name>.md`, and every `region/<name>.md` gain the same four frontmatter fields that `campaigns/<name>.md` and `encounters/<campaign>/<name>.md` already carry: `created_by`, `created_on`, `updated_by`, `updated_on` (git user name + UTC timestamp, format `%Y-%m-%dT%H:%M:%SZ`).
- `created_by`/`created_on` are stamped exactly once, when the object first comes into existence (`world.initialize_world`'s `created` branch; `lore.create_lore`; `region.create_region`), and never rewritten afterward.
- `updated_by`/`updated_on` are stamped (also seeded on creation, matching `created_*`) on every subsequent write to the object's own file, mirroring which `campaign.py`/`encounter.py` functions already do this:
  - `world.py`: `set_attribute`, `update_body`, and the world-side write inside `assign_lore`/`unassign_lore` (i.e. `_update_assigned_lore`).
  - `lore.py`: `update_lore`, `set_summary`, `set_enabled`, `set_assigned_to_world`, and `add_assigned_region`/`remove_assigned_region` (i.e. `_update_assigned_regions`) - this covers the lore-side write that happens when a region assigns/unassigns it, and when the world assigns/unassigns it.
  - `region.py`: `update_region`, `set_summary`, `set_path`, and the region-side write inside `assign_lore`/`unassign_lore` (i.e. `_update_assigned_lore`).
- This is a forward-only change: existing `.sourcebook` files created before this encounter (including this repo's own current `world.md`, `lore/*.md`, and `region/*.md`) are **not** backfilled. No migration or one-time backfill command is in scope.
- No template changes: as with `campaign.md`/`encounter.md` today, the four fields are stamped in code after loading the template, not declared in `templates/sourcebook/{world,lore,region}.md`.
- `cac bootstrap init` (via `cli/bootstrap.py`'s `init`, which calls `world_core.initialize_world`) must still fail cleanly - not with a raw traceback - if git identity can't be resolved, since `initialize_world` will now be able to raise `GitIdentityError` for the first time.
- Every mutating CLI command in `cli/world.py`, `cli/lore.py`, and `cli/region.py` that now flows through a stamping call must catch `GitIdentityError` and route it through `fail(console, str(exc))`, matching `cli/campaign.py`'s existing pattern - today none of these three CLI modules import or catch it at all.
- No MCP tool changes: `world_get`/`lore_get`/`region_get` already surface the full raw frontmatter dict via `read_metadata`/`read_world`'s `metadata` field, so the four new keys appear automatically. `lore_to_dict`/`region_to_dict` (used for create/update/etc. mutation responses) stay as they are today (`name`+`body`, or `name`+`path`+`body`) - they already omit other existing frontmatter fields like `enabled`/`assigned_to_world`, so this is consistent, not a new gap.
- No change to `list_lore`/`list_regions`/`list_campaigns_with_status` ordering (alphabetical by name, unchanged). Whether lore/region ever get an `updated_on`-ordered listing, or join the search index, is explicitly out of scope for this encounter - see Rationale.

## Rationale

`campaign.py` and `encounter.py` already stamp `created_by`/`created_on`/`updated_by`/`updated_on` via a private `_stamp_created`/`_stamp_updated` pair plus four `_KEY` constants - defined identically, verbatim, in both modules today (confirmed by inspection: same function bodies, same constant values). `world.py`, `lore.py`, and `region.py` have no equivalent, which is the gap this encounter closes, per GM direction: `encounter.list_encounters` already sorts a campaign's encounters by `updated_on` (oldest-updated first) and `search_index.py`'s `_reindex_encounters` already pulls `updated_on` out of encounter metadata for its index rows - both existing precedents for `updated_on` being load-bearing, machine-read data, not just a nice-to-have display field. The GM's stated reason for closing this gap now, during the `v0.1.2-encounter-indexing-and-search` campaign specifically, is that a "common index model" - i.e. `search_index.py` eventually indexing lore/region/world alongside encounters, the way `build-sqlite-fts5-encounter-index`'s Requirements left explicitly undecided ("Whether lore/region/world ever join search is explicitly **not** decided here") - needs `updated_on` to already exist on those objects before that extension can be designed, the same way it already exists on encounters today. This encounter only adds the fields; it does not decide or implement that future indexing extension, and does not change `list_lore`/`list_regions` ordering or add any lore/region/world rows to the FTS5 schema - those remain open decisions for a later encounter.

Given the pattern is about to be needed a third, fourth, and fifth time (`world.py`, `lore.py`, `region.py`), copying `_stamp_created`/`_stamp_updated` and the four `_KEY` constants a third time would leave five near-identical copies across the codebase. Per this project's own architecture split (`config.py` = "all directory/file names, regex patterns, and status enums in one place"; `frontmatter_utils.py` = "shared helpers ... for reading/writing YAML-frontmatter markdown"), and mirroring the existing `SUMMARY_KEY` (in `config.py`) / `set_summary_attribute` (in `frontmatter_utils.py`) split, this encounter extracts the four key constants into `config.py` and the two stamping functions into `frontmatter_utils.py`, and updates `campaign.py`/`encounter.py` to import and use the shared versions instead of their local copies - a pure refactor with no behavior change for those two modules, verified by their existing test suites passing unmodified.

`clean-tests-and-lint` (assigned to the world) applies throughout. `console-best-practices` (assigned to the `crypts-and-commits` region) is not implicated - the new frontmatter values are printed by the existing generic `for key, value in metadata.items(): console.print(f"[bold]{key}[/bold]: {value}")` loops already present in `cli/world.py`, `cli/lore.py`, and `cli/region.py`'s `get` commands, which is unaffected by this change (a git user name and an ISO timestamp are not expected to contain Rich markup or need `markup=False`, matching how `campaign_get`'s CLI output already handles the identical fields today).

## Plan

1. **`core/config.py`**: add `CREATED_BY_KEY = "created_by"`, `CREATED_ON_KEY = "created_on"`, `UPDATED_BY_KEY = "updated_by"`, `UPDATED_ON_KEY = "updated_on"`.
2. **`core/frontmatter_utils.py`**: add `stamp_created(post: frontmatter.Post, root: Path) -> str` and `stamp_updated(post: frontmatter.Post, root: Path) -> str`, moved verbatim (adjusted to import the new key constants from `config` and call `git_utils.current_git_user`) from `campaign.py`'s current `_stamp_created`/`_stamp_updated`. This module will now import `git_utils` and the four new keys from `config`.
3. **`core/campaign.py`** and **`core/encounter.py`**: delete their local `_stamp_created`/`_stamp_updated` defs and the four local `_KEY` constants; import `stamp_created`/`stamp_updated` from `frontmatter_utils` (already imported as `frontmatter_utils` in both) and the four `_KEY` constants from `config` (both already import from `config`); update the handful of call sites (`_stamp_created(post, root)` -> `frontmatter_utils.stamp_created(post, root)`, etc.) and any reference to the old local constants (e.g. `encounter.py`'s `list_encounters` and `_validate_and_order`'s `sort_key`, both of which reference `UPDATED_ON_KEY`/`CREATED_ON_KEY`). No behavioral change.
4. **`core/world.py`**: import `git_utils` and `frontmatter_utils` (for `stamp_created`/`stamp_updated`).
   - `initialize_world`: inside the `if created:` branch, after writing the template, load it back with `frontmatter.load`, call `frontmatter_utils.stamp_created(post, root)`, and `write_post` - creating the file with stamps on first bootstrap.
   - `set_attribute`: call `frontmatter_utils.stamp_updated(post, root)` before `write_post`.
   - `update_body`: call `frontmatter_utils.stamp_updated(post, root)` before `write_post`.
   - `_update_assigned_lore`: call `frontmatter_utils.stamp_updated(post, root)` before `write_post` (covers both `assign_lore` and `unassign_lore`'s world-side write).
5. **`core/lore.py`**: import `git_utils` and `frontmatter_utils`.
   - `create_lore`: call `frontmatter_utils.stamp_created(post, root)` before `write_post`.
   - `update_lore`: call `frontmatter_utils.stamp_updated(post, root)` before `write_post`.
   - `set_summary`: call `frontmatter_utils.stamp_updated(post, root)` before `write_post`.
   - `_set_flag` (covers both `set_enabled` and `set_assigned_to_world`): call `frontmatter_utils.stamp_updated(post, root)` before `write_post`.
   - `_update_assigned_regions` (covers both `add_assigned_region` and `remove_assigned_region`): call `frontmatter_utils.stamp_updated(post, root)` before `write_post`.
6. **`core/region.py`**: import `git_utils` and `frontmatter_utils`.
   - `create_region`: call `frontmatter_utils.stamp_created(post, root)` before `write_post`.
   - `update_region`: call `frontmatter_utils.stamp_updated(post, root)` before `write_post`.
   - `set_summary`: call `frontmatter_utils.stamp_updated(post, root)` before `write_post`.
   - `set_path`: call `frontmatter_utils.stamp_updated(post, root)` before `write_post`.
   - `_update_assigned_lore`: call `frontmatter_utils.stamp_updated(post, root)` before `write_post` (covers both `assign_lore` and `unassign_lore`'s region-side write).
7. **`cli/world.py`**: import `GitIdentityError` from `cac.core.git_utils`; add it to the `except` tuple in `set_attribute` and `set_body`.
8. **`cli/lore.py`**: import `GitIdentityError`; add it to the `except` tuple in `create_lore`, `update_lore`, `set_summary`, `assign_world`, `unassign_world`, `assign_region`, `unassign_region`, `enable_lore`, `disable_lore`.
9. **`cli/region.py`**: import `GitIdentityError`; add it to the `except` tuple in `create_region`, `update_region`, `set_summary`, `set_path`.
10. **`cli/bootstrap.py`**: import `GitIdentityError`; wrap the `world_core.initialize_world(root)` call so `GitIdentityError` routes through a clean failure message (matching the `fail(console, str(exc))` pattern used elsewhere) instead of an unhandled traceback, since this is the one call site that could previously never raise it and now can.
11. **Tests** (mirroring `tests/core/test_campaign.py`'s existing patterns exactly - `_set_identity`/`_default_identity` autouse fixture monkeypatching `git_utils.current_git_user` and `frontmatter_utils.utcnow`; `test_create_campaign_sets_created_and_updated_fields`; `test_update_campaign_refreshes_updated_but_not_created`; `test_create_campaign_propagates_git_identity_error`):
    - `tests/core/test_campaign.py`, `tests/core/test_encounter.py`: run unmodified and must still pass, proving step 3's refactor is behavior-preserving.
    - `tests/core/test_world.py`: add the `_set_identity`/`_default_identity` fixture pair; update `test_read_world_returns_metadata_and_body`'s exact `metadata ==` assertion to include the four new deterministic keys/values; add tests analogous to campaign's for `initialize_world` (created-and-updated stamped identically on first creation, second `initialize_world` call on an existing file does not restamp), `set_attribute` and `update_body` (bump `updated_*`, leave `created_*` alone), `assign_lore`/`unassign_lore` (world's own `updated_*` bumped), and git-identity-error propagation for `initialize_world`, `set_attribute`, `update_body`, `assign_lore`.
    - `tests/core/test_lore.py`: same identity-fixture addition; add analogous stamp tests for `create_lore`, `update_lore`, `set_summary`, `set_enabled`, `set_assigned_to_world` (including via `world.assign_lore`/`unassign_lore` triggering the lore-side stamp), `add_assigned_region`/`remove_assigned_region` (including via `region.assign_lore`/`unassign_lore`), plus git-identity-error propagation for `create_lore` and `update_lore`.
    - `tests/core/test_region.py`: same identity-fixture addition; add analogous stamp tests for `create_region`, `update_region`, `set_summary`, `set_path`, `assign_lore`/`unassign_lore` (region's own `updated_*` bumped), plus git-identity-error propagation for `create_region` and `update_region`.
    - `tests/cli/test_world.py`, `tests/cli/test_lore.py`, `tests/cli/test_region.py`: add `_break_git_identity` helper (mirroring `tests/cli/test_campaign.py`) and one `test_<command>_fails_when_git_identity_unresolvable` per mutating command touched in steps 7-9.
    - `tests/cli/test_bootstrap.py` (or wherever `cac bootstrap init` is currently tested - locate via search): add a test that `init` exits non-zero with a clean message, not a traceback, when git identity is unresolvable.

## Verification

- `pdm run pytest -q` passes, including every new/updated test above, with no skips or deletions used to dodge a failure.
- `pdm run ruff check .` reports zero errors and `pdm run ruff format .` reports no diffs.
- Manually run `cac world get`, `cac lore get <name>`, `cac region get <name>` against this repo's own `.sourcebook` after creating a fresh lore/region entry and confirm `created_by`/`created_on`/`updated_by`/`updated_on` appear and look correct; confirm this repo's pre-existing `world.md` and any pre-existing lore/region entries are unchanged (no backfill) until next touched.
- Confirm `mcp__crypts-and-commits__world_get`/`lore_get`/`region_get` surface the same four fields without any MCP-layer code change.

## Log

### Review - 2026-07-27T03:35:53Z - John Hoff

Plan is well-grounded — every factual claim about existing code (identical _stamp_created/_stamp_updated in campaign.py/encounter.py, named function existence in world.py/lore.py/region.py, unguarded initialize_world call in cli/bootstrap.py, raw-metadata passthrough in mcp/world.py/mcp/lore.py/mcp/region.py) checks out on inspection, and it fully honors the one formally-applicable lore item, clean-tests-and-lint, via its Verification section. The encounter initially had no regions assigned despite its Plan touching only packages/crypts-and-commits, which is exactly the crypts-and-commits region's path — a region carrying cli-mcp-parity and console-best-practices, both plausibly relevant here. The reviewer checked both directly: console-best-practices is satisfied (the new fields print via existing CLI-authored key/value loops, not stored-body content) and cli-mcp-parity is satisfied by precedent (mcp/campaign.py already has zero exception handling for its own GitIdentityError-raising core calls, so not adding equivalent catches to mcp/world.py/mcp/lore.py/mcp/region.py here is consistent, not a new gap) — but the applicable-lore gate itself would not have surfaced either check had the reviewer not gone beyond it, since neither lore item was in scope for an unassigned encounter. The encounter has since been assigned to the crypts-and-commits region so the gate now reflects what was actually checked.

### Completed - 2026-07-27T03:50:36Z - John Hoff

Verification passed: pdm run pytest -q (637 passed, no skips), ruff check . and ruff format . --check both clean. Manually verified via cac lore create/cac region create (then deleted) that created_by/created_on/updated_by/updated_on appear correctly on fresh entries, and confirmed this repo's own pre-existing world.md is untouched (no backfill, as designed). Refactored the duplicated _stamp_created/_stamp_updated pair out of campaign.py/encounter.py into shared frontmatter_utils.stamp_created/stamp_updated (keys in config.py); world.py/lore.py/region.py now stamp created_* once on creation and updated_* on every mutating write, including the cross-object lore<->world and lore<->region assignment writes. Added GitIdentityError handling to every mutating CLI command in cli/world.py, cli/lore.py, cli/region.py, and to cli/bootstrap.py's init. Noted for the record: this repo's own live MCP server process predates these edits, so lore_get/region_get/world_get called through MCP in-session still reflected pre-fix behavior until restarted - confirmed correct behavior via the CLI instead, which starts a fresh process each invocation.
