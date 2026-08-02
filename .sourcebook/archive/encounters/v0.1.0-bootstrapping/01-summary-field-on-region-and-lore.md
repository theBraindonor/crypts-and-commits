---
archived: true
campaign: v0.1.0-bootstrapping
created_by: John Hoff
created_on: '2026-07-25T01:22:23Z'
name: 01-summary-field-on-region-and-lore
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-08-02T22:00:20Z'
---

# Summary Field on Region and Lore

## Requirements

- Add a `summary` frontmatter field to both `region` and `lore` objects.
- The field is capped at 500 characters; a write exceeding the cap is rejected with a clear, actionable error.
- Its purpose is a routing signal: enough for an agent to decide whether it needs to read the full body. It is not a substitute for the body.
- On read, when a `summary` is absent, the read path returns an explicit placeholder message stating the summary does not exist (never a blank/empty value), so the agent knows to fall back to reading the body.
- `world` and `campaign` do NOT get a `summary` field (world is served full; campaign is served full).
- Additive frontmatter only — no change to how bodies are stored.
- This encounter establishes the data model plus a direct means to set/store the field. The generate-and-approve workflow and write-transition wiring are a separate encounter (02).

## Rationale

Per `docs/context-management-design.md`, summaries are the bounded projection that lets deterministic aggregation (the context prime) scale as the corpus grows: region/lore are served as summaries in the prime bundle, with full bodies hydrated on demand. Capping at 500 characters keeps the primed payload predictable. The explicit "no summary" placeholder prevents an agent from mistaking an absent summary for "nothing to know." Scope is deliberately the storage layer only; how summary *content* is drafted and approved is encounter 02.

## Plan

1. `core/config.py`: add a `SUMMARY_KEY` constant and a `SUMMARY_MAX_LENGTH = 500` constant, alongside the existing key constants.
2. `core/lore.py` and `core/region.py`: read the summary field; add a direct setter that enforces the 500-char cap; add a read helper that returns the stored summary or the explicit placeholder message when absent.
3. `cli/lore.py` / `cli/region.py`: surface the summary on `get` (with `markup=False`, per `console-best-practices`) and expose a minimal way to set it.
4. Tests mirror source (`tests/core/test_lore.py`, `test_region.py`, `test_config.py`, and the matching `cli` tests): cap enforcement, placeholder-when-absent, round-trip, on both region and lore.
5. `clean-tests-and-lint`: `pdm run pytest -q` and `ruff check`/`format` clean.

## Verification

- `pdm run pytest -q` passes with new coverage for the summary field (cap enforcement, placeholder-when-absent, round-trip) on both region and lore.
- `pdm run ruff check .` / `pdm run ruff format .` clean.
- Manual: set a summary on a region and a lore; `cac ... get` shows it; an object without a summary shows the explicit placeholder rather than a blank.

## Log

### Review - 2026-07-25T01:28:45Z - John Hoff

Reviewed against the two applicable lore items. clean-tests-and-lint is honored: Plan step 5 and Verification commit to pytest -q plus ruff check/format clean, with concrete new coverage (cap, placeholder-when-absent, round-trip) and no skip/noqa routing. console-best-practices is honored: the summary is stored user content and Plan step 3 correctly surfaces it with markup=False; the one load-bearing caveat is that summary must NOT be emitted through the existing markup=True frontmatter loop in the get commands but given its own markup=False print like the body, or bracketed summary text will be silently stripped. Logic placement (cap/read-helper/placeholder in core, cli only surfacing) matches the region's thin-wrapper architecture rule. Rationale's reference to docs/context-management-design.md is design justification, not lore, and was not verified. PASS-WITH-NOTES.

### Completed - 2026-07-25T01:40:07Z - John Hoff

Implemented the summary field on region and lore: SUMMARY_KEY/SUMMARY_MAX_LENGTH=500 in config; shared cap-enforcing setter, placeholder helper, and SummaryTooLongError in frontmatter_utils; set_summary/read_summary wrappers in core lore and region (error re-exported for the CLI); get commands render the summary via a dedicated markup=False print kept out of the markup=True frontmatter loop; new set-summary CLI commands. Verification green: 383 tests pass, ruff check/format clean, manual get shows stored summary or explicit placeholder. Summaries also populated on all three regions and both lore entries.
