---
archived: false
campaign: c001-boss-edition
created_by: John Hoff
created_on: '2026-10-28T03:05:50Z'
depends_on:
- e017-fix-review-findings-and-supported-continuation-reads
kind: scripted
name: e018-exact-canonical-names-win-short-reference-resolution
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-10-28T03:19:52Z'
---

## Requirements

Make every retained record reachable by its exact canonical name. This reverses one rule from e008: an input that exactly equals an existing record's canonical name selects that record, even when the name is shaped like a short ref.

Today `Inventory.resolve` (`packages/crypts-and-commits/src/cac/core/references.py`) treats any input matching `SHORT_REFERENCE_PATTERN` as a short ref before checking for an exact name. Suppose a legacy record is literally named `c001`, `b001` or `e001`, and a numbered sibling with the same number exists in the same scope, such as `c001-mvp`. Then resolving `c001` raises `AmbiguousReferenceError`, and no MCP or CLI input can address the literal record. There is no rename operation either, so its only escape is a direct file edit, which the guardrail forbids. Search can find it, but every get and mutation addresses records by name.

New rule, applied to boss, campaign and encounter scopes, and to both parts of a qualified `cNNN/eNNN` ref:

1. **Exact name wins.** If the input exactly matches a canonical name in the scope's live+archive inventory, select that record.
2. **Otherwise numeric resolution applies unchanged.** The input resolves by number when exactly one record matches. Different paddings of the same number (`c0001` vs `c001`), wrong-domain refs and zero IDs behave as before. Any other multiple match still fails as ambiguous.
3. **Identity follows the selection rule.** A record's `identity.short` is usable only if resolving it returns that same record. In the collision case, the literal `c001` gets short `c001`, and `c001-mvp` gets short null with reason `ambiguous`; it stays reachable by its full name. Qualified encounter identities follow their parent campaign's identity as they do now.
4. **The rest is unchanged.** Live/archive duplicate canonical files remain integrity errors. Create names stay literal. Dependency canonicalization and missing-literal-edge removal, qualified-context rules, and all lifecycle, closed-campaign and archive guards are unchanged. Nothing is renamed, migrated or written by resolution.

The tradeoff is accepted by the developer. In this rare collision, typing `c001` while meaning `c001-mvp` now silently selects the legacy record instead of failing. The response's `identity` shows which record was selected.

Update `packages/crypts-and-commits/src/cac/core/templates/docs/workflow.md` (the "historical literal name" paragraph under resolution) and any directly conflicting wording in `docs/boss-edition.md` in the same change. Keep `workflow.md` within its unchanged 64,000-character `DOCS_RESPONSE_BUDGET`; it is currently about 63,567 characters. No CLI/MCP signature changes, no new tools, no schema change, and no skill changes are needed.

## Rationale

The campaign review found that e008's no-shadowing rule leaves a legacy short-shaped record with no supported address. That conflicts with the guardrail, which says managed content is reached only through MCP/CLI. Search does not help, because reading and acting still require naming the record. Of the three options considered (exact-name precedence, new escape syntax, or documented manual repair), the developer chose exact-name precedence. It makes every record reachable without new input grammar, and the silent-selection risk is confined to an unusual legacy collision whose result is visible in `identity`.

## Plan

1. Prime through world-manager and confirm campaign state. Use CodeGraph to inspect `references.Inventory.resolve`, `Inventory.identity`, `Inventory.encounter` and `select`, and their callers in `packages/crypts-and-commits/src/cac/core/references.py`. Read `tests/core/test_references.py`, `tests/cli/test_references.py` and `tests/mcp/test_references.py` under `packages/crypts-and-commits/`.
2. In `Inventory.resolve`, check exact membership in the scope's inventory before short-ref numeric matching. Confirm that `identity()` then reports the outcomes in Requirement 3 without further change, and adjust it only if it does not. Leave storage validation, duplicate-file detection, `missing_literal` handling and error types as they are.
3. Tests:
   - Replace `test_short_looking_literal_does_not_shadow_numbered_record`, which asserts the rule being reversed, with tests of the new rule for boss, campaign and qualified encounter scopes.
   - The literal record is reachable and identity-usable. Its numbered sibling is reachable by full name with short null/`ambiguous`. A padded alternative still fails as ambiguous.
   - Two numbered siblings with no literal record still fail as ambiguous.
   - Archived literal records resolve too.
   - Add one end-to-end check each through MCP and CLI get, for example `campaign_get("c001")` and `cac campaign get c001`.
   - Explain the replaced test in an encounter message.
4. Update the `workflow.md` paragraph and any conflicting `docs/boss-edition.md` text. Verify the guide size.
5. Run focused reference tests, then `pdm run pytest -q`, `pdm run ruff check .` and `pdm run ruff format .`. Record results and ask for developer confirmation before completing.

## Verification

- The new resolution and identity matrix above passes for all three scopes, including archived records and qualified refs. Pre-existing ambiguity, padding, duplicate-file, dependency and qualified-context tests pass unchanged; the only replaced test is the one encoding the reversed rule.
- `campaign_get("c001")` and `cac campaign get c001` select the literal record when `c001-mvp` coexists, and `c001-mvp` remains reachable by full name.
- `workflow.md` describes exact-name precedence and remains fully retrievable at the unchanged budget.
- `pdm run pytest -q` passes, and `pdm run ruff check .` and `pdm run ruff format .` are clean, with no skips, suppressions or weakened tests.

## Log

### Review - 2026-10-28T03:07:38Z - John Hoff

Reviewed against clean-tests-and-lint, cli-mcp-parity, console-best-practices, skills-authored-only-in-templates and workflow-doc-source-of-truth; the plan is consistent with all of them. The change is confined to core/references.py with no CLI/MCP signature or tool changes, and parity is confirmed by one end-to-end get check per surface. workflow.md (and any conflicting docs/boss-edition.md text) is updated in the same change, with a size check against the unchanged 64,000-character budget. The test gate requires clean pytest and ruff with no skips or suppressions. The one replaced test encodes the e008 rule being reversed, its replacement is explained in an encounter message, and the new matrix covers boss, campaign and qualified encounter scopes, archived records, padded-ref ambiguity, and numbered siblings with no literal record. Notes for execution: (1) check the shared MCP tool description text ("...reject ambiguity") and the skill templates for wording that states the old short-ref-first rule, and update them, or record that they don't conflict, because the claim that no skill changes are needed isn't backed by a cited check; (2) workflow.md has only about 430 characters of headroom, so plan to trim nearby wording rather than raise the budget if the new paragraph is longer; (3) confirm that no caller of Inventory.resolve (dependency canonicalization, qualified-context checks) depends on the short-ref-first ordering.

### Opened - 2026-10-28T03:08:40Z - John Hoff

Developer approved execution following independent PASS-WITH-NOTES review.

### Message - 2026-10-28T03:15:09Z - John Hoff

Implementation and verification finished; awaiting developer confirmation.

Change: Inventory.resolve returns an exact canonical inventory match before any short-ref parsing. Numeric resolution, padding ambiguity, missing_literal edge removal, duplicate-file integrity errors and error types are unchanged. identity() needed no change: a literal c001 now reports short c001, and its numbered sibling reports short null/ambiguous. A side effect within the same rule: a legacy name shaped like another domain's ref (a campaign named b001) is now reachable by exact name, where before it was rejected as a wrong-domain short ref.

Review note 3: every Inventory.resolve caller (select, Inventory.campaign, Inventory.encounter for both qualified parts, identity, campaign_bosses.resolve, rumors._owner, boss dependency inputs) only gains exact-name precedence. missing_literal is still applied only after the exact check, so missing-edge removal behaves as before.

Tests replaced because they encoded the reversed e008 rule: core test_short_looking_literal_does_not_shadow_numbered_record, and literal-identity assertions in cli test_references (now test_create_is_literal_and_exact_name_selects_it), mcp test_references test_creations_are_literal_and_campaign_selection_is_short, and mcp test_coupling test_literal_campaign_creation_name_and_broken_origin_diagnostics. Their safety intent is kept: a b001 update never touches b001-original, and a padded b0001 still fails as ambiguous.

New tests: an exact-name matrix for boss, campaign and encounter, live and archived; numbered siblings without an exact match stay ambiguous; qualified refs use exact names in both parts; a wrong-domain-shaped literal is reachable; and MCP campaign_get("c001") and CLI cac campaign get c001 select the legacy record. Removing only the new early return makes exactly these 13 tests fail and all others pass.

Review note 1: skill templates only say "ambiguous short refs need canonical names", which is still true, so no skill change. docs/boss-edition.md has no conflicting text. The shared MCP target description now says "exact canonical names win". Note 2: the workflow.md paragraph was rewritten and the guide is 63,552 characters.

Checks: pdm run pytest -q passed 1555 tests; ruff check and format are clean; git diff --check is clean.

### Completed - 2026-10-28T03:19:52Z - John Hoff

Developer confirmed completion. An exact canonical name now selects its record before short-ref parsing, so short-shaped legacy names stay reachable while numeric ambiguity and padding guards are unchanged. Verification: 1555 tests passed, Ruff clean, git diff --check clean, and the 13 new or updated tests fail without the change. The rebuilt MCP server advertises the updated target description.
