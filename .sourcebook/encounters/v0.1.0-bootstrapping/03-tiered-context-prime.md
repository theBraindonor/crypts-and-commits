---
campaign: v0.1.0-bootstrapping
created_by: John Hoff
created_on: '2026-07-25T01:22:26Z'
name: 03-tiered-context-prime
regions:
- crypts-and-commits
status: draft
updated_by: John Hoff
updated_on: '2026-07-25T01:23:00Z'
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
