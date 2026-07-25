---
campaign: v0.1.0-bootstrapping
created_by: John Hoff
created_on: '2026-07-25T01:22:23Z'
name: 01-summary-field-on-region-and-lore
regions:
- crypts-and-commits
status: draft
updated_by: John Hoff
updated_on: '2026-07-25T01:22:57Z'
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
