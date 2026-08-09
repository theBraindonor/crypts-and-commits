---
archived: false
campaign: v0.1.8-release-readiness
created_by: John Hoff
created_on: '2026-08-05T02:41:54Z'
depends_on: []
name: add-unscripted-encounter-subtype
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-08-09T01:16:26Z'
---

# Encounter

## Requirements

- Introduce an "unscripted encounter" subtype that captures manual changes made by the developer or the coding assistant outside the context of a pre-planned encounter, so the intent behind those changes is preserved for subsequent agent use.
- Represent the subtype as a new encounter frontmatter field (e.g. `kind`), defaulting to the existing behavior ("scripted") for every current and future normally-planned encounter, with "unscripted" as the alternate value.
- An unscripted encounter follows the same `draft` -> `reviewed` -> `open` -> `completed` (or `abandoned`) status lifecycle as a scripted encounter, including the independent-reviewer gate at `draft` -> `reviewed` and the developer approval gates around it - but only `Requirements` and `Rationale` are required/applicable. `Plan` and `Verification` are not applicable to this kind and must not be enforced the way they are (implicitly, by convention) for scripted encounters.
- Region assignment remains required before review, unchanged from scripted encounters.
- The subtype must be surfaced consistently across `core/encounter.py`, `cli/encounter.py`, `mcp/encounter.py`, and `docs/workflow.md`, per the `cli-mcp-parity` and `workflow-doc-source-of-truth` region lore.
- The subtype must also be surfaced in the `campaign-manager` skill templates (`templates/skills/{claude,codex}/campaign_manager/SKILL.md`), since that is where the draft-step instructions and the reviewer-subagent prompt currently assume every encounter has a Plan to write and review. Without this, an agent following the skill as worded today would either force a Plan/Verification onto an unscripted encounter or have the reviewer wrongly treat a missing Plan as a defect.

## Rationale

Today, `.sourcebook` only models work that goes through the full plan-first encounter flow. In practice, both the developer and the coding assistant sometimes make manual changes outside that flow - direct edits, quick fixes, exploratory changes - and that work's *intent* currently has nowhere to be recorded, so a later session has no way to recover why it happened.

An unscripted encounter gives that manual work a place to be captured after the fact: Requirements and Rationale describe what was done and why, without forcing a Plan/Verification that don't apply to work that's already happened. Running the encounter through the same full review lifecycle (rather than skipping straight to a closed/recorded state) is deliberate: it gives the independent reviewer a chance to check the recorded intent against project lore, and gives the coding assistant an opportunity to make follow-up changes based on that review - the same value the review gate provides for scripted encounters, just applied to a record of completed work instead of a plan for future work.

The reviewer-prompt and draft-step wording live only in the `campaign-manager` skill templates, not in `core`/`cli`/`mcp` - so realizing this value end-to-end (not just storing a `kind` field) requires updating those templates in the same change, per `skills-authored-only-in-templates`.

## Plan

1. **`core/config.py`** - add `ENCOUNTER_KIND_KEY = "kind"`, `ENCOUNTER_KINDS = ("scripted", "unscripted")`, `DEFAULT_ENCOUNTER_KIND = "scripted"`.

2. **Templates** (`core/templates/sourcebook/`):
   - `encounter.md` (existing, scripted): add `kind: "scripted"` to the frontmatter block, unchanged otherwise.
   - `encounter_unscripted.md` (new): frontmatter `name`/`campaign`/`status: "draft"`/`kind: "unscripted"`/`regions: []`/`depends_on: []`/`archived: false`, and a body with only `# Encounter`, `## Requirements`, `## Rationale` - no `Plan`/`Verification` headings, since they're not applicable to this kind.

3. **`core/encounter.py`**:
   - Add `InvalidEncounterKindError(ValueError)`.
   - `Encounter` dataclass: add a `kind: str` field.
   - Replace the single `_TEMPLATE_FILENAME` constant with a `{"scripted": "encounter.md", "unscripted": "encounter_unscripted.md"}` mapping.
   - `template_body(kind: str = DEFAULT_ENCOUNTER_KIND) -> str`: validate `kind` against `ENCOUNTER_KINDS` (raise `InvalidEncounterKindError` if not), load the matching template.
   - `create_encounter(root, campaign, name, body, kind=DEFAULT_ENCOUNTER_KIND)`: validate `kind`, load the matching template for frontmatter defaults, set `post["kind"] = kind`, keep existing name/campaign/content/stamp behavior otherwise.
   - `_to_encounter`: read `kind` via `post.get(ENCOUNTER_KIND_KEY, DEFAULT_ENCOUNTER_KIND)`.
   - No changes to `update_encounter`/`review_encounter`/`open_encounter`/`complete_encounter`/`abandon_encounter`/`record_message`: section presence isn't code-enforced for scripted encounters today either, so none is added for unscripted - the distinction stays template- and skill-level, per Requirements. `kind` is immutable after creation - no setter/assign-kind operation, matching the Requirements' silence on changing it later.

4. **`cli/encounter.py`**:
   - `create`: add `kind: str = typer.Option("scripted", "--kind", "-k", help="Encounter subtype: 'scripted' (default; Plan/Verification apply) or 'unscripted' (records already-done work; only Requirements/Rationale apply).")`; seed the editor body via `encounter_core.template_body(kind)`; pass `kind=kind` to `encounter_core.create_encounter`; catch `encounter_core.InvalidEncounterKindError` alongside the command's existing exceptions.
   - Add a short clause to the `app` Typer help docstring noting the `kind` distinction.

5. **`mcp/encounter.py`**:
   - `encounter_to_dict`: add `"kind": encounter.kind`.
   - `encounter_create(name, body, campaign=None, kind="scripted")`: pass `kind` through to `encounter_core.create_encounter`; update the docstring to mention it. No new MCP tool is needed - `kind` rides on the existing `encounter_create`/`encounter_get` tools, so `cli-mcp-parity` is satisfied without a new entry in `mcp/server.py`'s `_TOOL_MODULES` or a change to `test_all_domain_tools_are_registered`.

6. **`docs/workflow.md`** (`templates/docs/workflow.md`), Encounter section:
   - Add `kind` to the Frontmatter bullet, describing both values and the `scripted` default.
   - Add a short paragraph explaining `unscripted` encounters: same status lifecycle and review/approval gates, but only `Requirements`/`Rationale` are meaningful; the reviewer checks recorded intent against lore instead of a Plan.
   - Note `kind` as an optional, creation-time-only argument on the `encounter_create`/`cac encounter create` row.

7. **`templates/skills/claude/campaign_manager/SKILL.md`** and **`templates/skills/codex/campaign_manager/SKILL.md`**:
   - Note `encounter_create`'s `kind` argument in the Encounters tool list.
   - In the `draft` lifecycle prose, branch on kind: unscripted encounters only get Requirements/Rationale written (the `encounter_unscripted` template already omits Plan/Verification).
   - In the reviewer subagent prompt template, make the lore-check instruction conditional: for `unscripted`, check Requirements/Rationale (the recorded intent) against lore instead of a Plan, and make clear an absent Plan/Verification on an unscripted encounter is not itself grounds for REJECT/NOT-REVIEWABLE.
   - Leave the three explicit user gates (workflow.md's "Explicit user gates" section) untouched - they apply identically regardless of kind.
   - State explicitly that this is a template-only edit; the developer (never the agent) must run `cac bootstrap init` afterward to deploy it.

8. **Tests** (mirroring `src/cac/`, per the `crypts-and-commits` region's own convention):
   - `tests/core/test_encounter.py`: default kind on create, explicit `kind="unscripted"`, invalid kind raises `InvalidEncounterKindError`, `template_body("unscripted")` omits Plan/Verification headings, `read_encounter`/`_to_encounter` surfaces `kind`.
   - `tests/cli/test_encounter.py`: `--kind unscripted` create, default omits the flag, invalid `--kind` value fails cleanly.
   - `tests/mcp/test_encounter.py`: `encounter_create(..., kind="unscripted")` round-trips, `encounter_to_dict` includes `kind`.

## Verification

- `pdm run pytest -q` passes in full (not just the touched modules), and `pdm run ruff check .` / `pdm run ruff format .` are clean, per the `clean-tests-and-lint` world lore.
- Manually exercise both kinds end-to-end against a scratch campaign/encounter (not this repo's real `.sourcebook` state): `cac encounter create <name> --kind unscripted --body ...` produces a file with `kind: unscripted` and a two-section body; `cac encounter get <name>` surfaces `kind` in its frontmatter listing automatically; a default `cac encounter create` (no `--kind`) still produces `kind: scripted` with all four sections. Clean up the scratch encounter afterward.
- Confirm `docs_get("workflow")` / `cac docs get workflow` reflects the new `kind` content.
- The SKILL.md template edits are verified by reading the updated template content directly (their correctness), not by exercising the deployed copy - deploying via `cac bootstrap init` is the developer's step, out of this encounter's Verification.

## Log

### Review - 2026-08-09T00:57:03Z - John Hoff

PASS-WITH-NOTES: the Plan correctly satisfies all five applicable lore items - clean-tests-and-lint (full pytest/ruff gate in Verification), cli-mcp-parity (the new `kind` field rides the existing `encounter_create`/`encounter_get` tools rather than needing a new MCP entry, correctly reasoned against the actual cli/encounter.py/mcp/encounter.py code), console-best-practices (not implicated, no new stored-content printing), skills-authored-only-in-templates (edits target only the packaged templates/skills/{claude,codex}/campaign_manager/SKILL.md and explicitly defer deployment to the developer via `cac bootstrap init`), and workflow-doc-source-of-truth (docs/workflow.md update included and verified in Verification). Spot-checking the Plan's factual claims against core/encounter.py, core/config.py, cli/encounter.py, mcp/encounter.py, the existing encounter template, and both campaign_manager/SKILL.md templates confirmed they're accurate, including the claim that section presence isn't code-enforced today so no lifecycle-code change is needed for unscripted encounters. One non-blocking completeness note: the Plan doesn't call for updating the SKILL.md frontmatter `description:` field or a few command docstrings that still describe encounters as universally having all four sections - worth a quick pass during implementation, but it's cosmetic and touches no cited lore.

### Completed - 2026-08-09T01:16:26Z - John Hoff

All Verification steps passed: pdm run pytest -q (804 passed), ruff check/format clean, manual CLI exercise in a scratch repo confirmed default kind=scripted (all four sections), --kind unscripted (Requirements/Rationale only), and rejection of an invalid --kind value, and `cac docs get workflow` reflects the new kind field and Kind subsection. The developer ran `cac bootstrap init` to deploy the updated campaign_manager SKILL.md templates into .claude/skills/ and .agents/skills/, confirmed via grep showing kind referenced in both deployed copies.
