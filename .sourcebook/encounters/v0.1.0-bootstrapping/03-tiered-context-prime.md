---
campaign: v0.1.0-bootstrapping
created_by: John Hoff
created_on: '2026-07-25T01:22:26Z'
name: 03-tiered-context-prime
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-07-25T02:13:30Z'
---

# Tiered Context Prime

## Requirements

- Add a core aggregation operation that assembles the global prime bundle in one call: world (full body) + world-assigned enabled lore (summaries) + region map (per region: `summary` + `path` + assigned-lore edge names) + active campaign (full body).
- Add an `applicable_lore` resolution for an encounter: enabled world-assigned lore plus enabled lore assigned to the encounter's region(s), returned as `{name, summary, ref}` entries for selective hydration.
- Selection (which lore/region applies) is computed live; summaries come from the stored field (encounter 01); full bodies are hydrated on demand and are NOT part of prime.
- The region map carries edges only (assigned-lore names), not region-specific lore summaries — those wait for region focus.
- Active-campaign "full" = the campaign body only, NOT its encounter list.
- Expose via CLI command(s) (e.g. a `prime` command and an applicable-lore command). Real logic lives in `core`; the CLI stays a thin wrapper.

## Rationale

Per `docs/context-management-design.md` (deterministic aggregation + tiered read + the global prime bundle). This collapses the current many-call chain (world get, lore list, lore get per item, region get, ...) into a single intent-based call, addressing round-trip churn. It depends on the summary field (encounter 01) so the bundle stays bounded. The traversal *procedure* for going deeper is documented in the skill (encounter 05), not embedded in this payload. Budget/truncation of the output is encounter 04.

## Plan

1. `core`: add aggregation function(s) that traverse world -> assigned lore, regions -> summaries + lore edges, and read the active campaign body (reuse `campaign.active_campaign`).
2. `core`: add `applicable_lore(encounter)` resolution (world-assigned enabled union region-assigned enabled), returning name/summary/ref.
3. `cli`: thin command(s) that print the assembled bundle with `markup=False` (per `console-best-practices`).
4. Tests mirror source: bundle assembly, edges-only region map, campaign-body-not-encounters, applicable-lore resolution across world + region assignment.
5. `clean-tests-and-lint`.

## Verification

- `pdm run pytest -q` and `ruff check`/`format` clean, with coverage for the prime bundle shape and applicable-lore resolution.
- Manual (on this repo's live sourcebook): the prime command returns world full + world-lore summaries + region map (edges) + active campaign body in one call; applicable-lore for an encounter returns the correct resolved set.

## Log

### Review - 2026-07-25T02:06:13Z - John Hoff

Reviewed against both applicable lore items: clean-tests-and-lint (world-assigned) is honored via an explicit Verification-stage gate (pytest + ruff, no shortcuts), and console-best-practices (region-assigned to crypts-and-commits) is honored via an explicit markup=False commitment for the new CLI command(s) printing stored/aggregated content. The Plan's global-prime and applicable-lore design tracks the cited docs/context-management-design.md accurately (full world, lore summaries only, edges-only region map, campaign body without encounters, live selection vs. precomputed summary vs. on-demand body), and the named campaign.active_campaign reuse point exists in core/campaign.py. Unverified and flagged rather than checked: the encounter-01 summary-field dependency this work relies on, and the feasibility of the traversal against core/lore.py/core/region.py/core/world.py internals, both outside this review's bounded surface. No lore conflicts found.

### Completed - 2026-07-25T02:13:30Z - John Hoff

Implemented core/prime.py (assemble_prime, applicable_lore) and cli/prime.py (cac prime get, cac prime applicable-lore), wired into app.py. Added 32 tests across core/cli mirroring source structure. pdm run pytest -q: 428 passed. ruff check/format: clean. Manually verified cac prime get and cac prime applicable-lore 03-tiered-context-prime against this repo's live sourcebook - shapes match the design doc's global prime bundle and applicable-lore contracts.
