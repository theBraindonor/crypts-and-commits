---
archived: false
campaign: c002-rulings
created_by: John Hoff
created_on: '2026-11-21T02:36:06Z'
depends_on:
- e002-ruling-search-index
kind: scripted
name: e003-ruling-prime-exposure
regions:
- crypts-and-commits
status: draft
updated_by: John Hoff
updated_on: '2026-11-21T02:36:07Z'
---

## Requirements

Expose every untriaged (`recorded`) ruling in the global prime bundle, per `b005-ruling-records`: "Prime includes every `recorded` ruling, including rulings from completed campaigns that are still untriaged. Canonized rulings live on through lore, and noted rulings can be ignored."

- **New bundle fields** on `prime_get` / `cac prime get`, present whether or not a campaign is open:
  - **`recorded_rulings`**: one entry per live `recorded` ruling, in canonical-name order (so grouped by campaign and then encounter). Each entry is `{name, campaign, encounter, summary}`, with `encounter` null for `e000`. Entries are routing data, like lore summaries: no bodies, origins, history or resolution. Callers hydrate with `ruling_get(name)`.
  - **`recorded_ruling_count`**: the exact number of valid recorded rulings found, even when entries are cut for the budget.
  - **`ruling_diagnostics`**: entries `{code: "invalid_ruling", ruling, message}`. One malformed ruling record (bad metadata, an inconsistent name) is reported here instead of failing the whole bundle, mirroring `active_boss_diagnostics`. A storage-level listing failure, such as an invalid filename in `rulings/`, is reported once with `ruling: null`. Messages are capped at 300 characters.
- **Scope.** `canonized` and `noted` rulings are excluded, and so are archived rulings (only canonized or noted rulings can be archived). Recorded rulings from every campaign are included, whatever that campaign's status. Prime never writes anything.
- **Budget.** The bundle still shares one response budget.
  - Existing behavior is unchanged: bodies (world, campaign, bosses) are cut first, with hydration refs.
  - If the bundle still does not fit after the bodies are emptied, trailing `recorded_rulings` entries are dropped. This adds one explicit truncation `{field: "recorded_rulings", notice: "TRUNCATED", ref: {tool: "ruling_list", status: "recorded"}}`. `recorded_ruling_count` and the diagnostics are never cut, so the omission is never silent.
  - If the remaining metadata still cannot fit with zero ruling entries, the call fails as it does today. After entries are dropped, whatever space remains goes back to the bodies as before.
- **CLI rendering.** `cac prime get` adds a `== Recorded Rulings ==` section after Active Bosses:
  - the count, then one `name: summary` line per entry, printed literally (`markup=False`);
  - each diagnostic as compact JSON;
  - a "No recorded rulings." line when there are none.
  - The ruling truncation notice is printed with the existing truncation output.
- **Docs, in the same change:**
  - `templates/docs/tool-reference.md` Prime section: the three new fields, the entry shape, the diagnostics, and the ruling truncation rule. Rulings section: replace "not yet included in prime" with a pointer to prime's recorded rulings.
  - `templates/docs/workflow.md`: the Rulings section says recorded rulings appear in prime until triaged, and "Priming and the disclosure ladder" step 1 mentions recorded rulings. The guide stays within the 45,000-character test cap.
  - The `prime_get` MCP docstring and the `cac prime get` help name the recorded rulings.

## Rationale

b005 makes prime visibility of untriaged rulings a success criterion. Showing them during every orientation keeps unresolved decisions in view, both for execution sessions (so a recorded ruling is not contradicted unknowingly) and for planning sessions (which should clear them). Including rulings from completed campaigns is the developer's explicit choice. Untriaged rulings are expected to stay few, because planning dispositions and archives them.

**Summary-only entries** follow the disclosure ladder: prime routes, and bodies are hydrated on demand (`ruling_get`). This keeps the bundle small and predictable.

**Per-record diagnostics** follow the `active_boss_diagnostics` precedent, so one damaged ruling cannot block orientation.

**The budget rule is a deliberate refinement.** Today, routing entries (lore and regions) that cannot fit make the call fail. Rulings are an open-ended, accumulating list that a skipped planning round could let grow. So the list degrades explicitly instead: an exact count, a TRUNCATED notice and a `ruling_list(status="recorded")` hydration ref. Information is never silently dropped, and orientation keeps working.

**Out of scope:**
- Skill template text describing the prime bundle and ruling capture or triage procedure (a later c002 encounter).
- `prime_applicable_lore`, which stays lore-only.
- Any change to rumors, which remain outside prime.

## Plan

1. **`core/prime.py`:**
   - Add `RulingSummary(name, campaign, encounter, summary)`.
   - Add `PrimeBundle` fields `recorded_rulings: list[RulingSummary]`, `recorded_ruling_count: int`, and `ruling_diagnostics: list[dict]`, all defaulted.
   - Add `_recorded_rulings(root)`:
     - list live names with `ruling.list_rulings(root)`, without a status filter, so one bad record cannot abort the listing; on failure, return a single `ruling: null` diagnostic;
     - for each name, `ruling.read_metadata` inside `try`, keeping `status == "recorded"` entries;
     - per-record errors (`ValueError`, `OSError`, `TypeError`, `KeyError`, `yaml.YAMLError`) become `invalid_ruling` diagnostics;
     - return entries, count and diagnostics.
   - Call it from `assemble_prime`.
   - In `present`, after the bodies are emptied, if the size still exceeds the budget, pop trailing `recorded_rulings` entries until it fits or the list is empty. Add the ruling truncation notice if any were dropped. Then apply the existing metadata check and refill the bodies.
2. **`cli/prime.py`:** add the Recorded Rulings section described in Requirements, and update the `get` help.
3. **`mcp/prime.py`:** update the `prime_get` docstring.
4. **Docs:** apply the `tool-reference.md` and `workflow.md` edits listed in Requirements.
5. **Tests:**
   - `tests/core/test_prime.py`:
     - With and without an open campaign, recorded rulings appear in name order with the entry shape, and `e000` gives `encounter: null`.
     - Canonized, noted and archived rulings are excluded.
     - A recorded ruling from a later-completed campaign still appears.
     - A malformed ruling file becomes an `invalid_ruling` diagnostic while the other rulings and the bundle still load.
     - An invalid filename in `rulings/` gives one `ruling: null` diagnostic.
     - Under a small `RESPONSE_BUDGET` with many rulings, entries are dropped from the end with the `ruling_list` truncation notice, `recorded_ruling_count` stays exact, and the payload fits.
     - At a budget too small for even the remaining metadata, the call still fails with the existing error.
     - Prime writes nothing.
   - `tests/cli/test_prime.py`: the Recorded Rulings section, including literal printing of bracketed summaries and the "No recorded rulings." line.
   - `tests/mcp/test_prime.py`: `prime_get` returns the three fields with a shape that matches core.
   - Update any existing test that asserts the exact bundle keys.

## Verification

- `pdm run pytest -q` passes, with no skips or deletions added to dodge failures.
- `pdm run ruff format .` has been applied, and then `pdm run ruff check .` and `pdm run ruff format --check .` are clean.
- A manual smoke test in a temporary scratch project, with the world seeded through core Python and never through `cac bootstrap init`:
  1. Open a campaign with an encounter.
  2. Record two rulings, one under the encounter and one under `e000`.
  3. `cac prime get` lists both under Recorded Rulings with a count of 2.
  4. Canonize one; prime lists only the other.
  5. Complete the campaign; the remaining recorded ruling is still listed.
  6. Note and archive it; prime shows "No recorded rulings."
- After the MCP server reconnects, a live `prime_get` in this repository lists this repo's two recorded c002/e001 rulings. This step is read-only.
- Docs describe exactly the shipped fields, shape, diagnostics and budget rule, checked against the diff.
