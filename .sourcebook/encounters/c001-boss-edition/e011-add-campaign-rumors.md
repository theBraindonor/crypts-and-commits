---
archived: false
campaign: c001-boss-edition
created_by: John Hoff
created_on: '2026-10-27T17:55:15Z'
depends_on:
- e009-add-boss-campaign-coupling
kind: scripted
name: e011-add-campaign-rumors
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-10-27T18:12:39Z'
---

## Requirements

Add optional campaign rumors as plain UTF-8 markdown documents, following the "Rumors: discoveries returned to planning" contract in docs/boss-edition.md.

- Store at most one document per existing campaign at bosses/rumors/<canonical-campaign-name>.md relative to the managed sourcebook root. Create storage lazily; a missing collection means no rumors. Do not create a boss record, frontmatter schema, status, required heading, summary, numbered rumor identity, or conversion bookkeeping. Preserve supplied text, including leading YAML-looking delimiters, brackets, Unicode, blank lines, and empty content.
- Expose `cac rumors list/get/create/update/delete` and matching `rumors_list/get/create/update/delete` MCP tools in this encounter. Campaign-targeting operations accept an optional campaign (active campaign fallback), canonical names and cNNN refs, return canonical identity, and reject missing or ambiguous campaigns. Create fails if the document exists; update/get/delete fail if absent. List discovers existing rumor documents across campaigns, including archived campaign owners, with cursor pagination and explicit diagnostics for orphaned documents.
- Rumors remain readable, editable, and deletable for completed, abandoned, and archived campaigns. These document operations must not inherit the terminal-status mutation lock for campaign bodies. Campaign completion, abandonment, reactivation, and archiving leave rumor bytes and location unchanged. No rumor archiving operation.
- CLI create/update accept mutually exclusive --body and --body-file using the shared body-input helper, with editor fallback when omitted. MCP requires an explicit body, including allowing an empty string. CLI delete uses the normal confirmation/--yes affordance; MCP deletion is unconditional. Stored text and user-originated diagnostics print literally.
- Keep responses bounded and CLI/MCP behavior equivalent. Get uses the existing body-budget/truncation convention for its initial response and provides a supported continuation read for oversized documents, rather than directing agents to inspect managed files. Document the continuation arguments/result and reject invalid cursors. Preserve existing shared get behavior for other domains.
- Validate canonical campaign names and storage containment before writes; reject unsafe paths, symbolic links/junctions, and file/directory collisions without modifying campaign, boss, or unrelated content.
- Rumors never count as bosses, reserve boss numbers, participate in boss references/dependencies/candidates, or alter boss/campaign links. No endpoint inspects Git branches. Document that execution branches edit their own rumors and planning may distill/edit/delete integrated rumors; capture alone does not change scope or create future work.

## Rationale

Implementation discoveries need a recoverable place without prematurely becoming bosses or expanding the current campaign. Freeform campaign-owned documents preserve that context through integration, while planning can distill or discard it later. Terminal and archived campaign ownership must not freeze these notes, because distillation commonly happens after the campaign ends. Simple document operations preserve the managed-content access guardrail without imposing an encounter-style workflow.

The active campaign is c001-boss-edition. Encounters e001 through e010 are completed. Depend on e009-add-boss-campaign-coupling for the shipped campaign/boss lifecycle and canonical-reference behavior this work must preserve. e009 transitively includes the body-file and boss storage prerequisites. No implementation is authorized by this draft.

## Plan

1. Inspect the relevant implementation under packages/crypts-and-commits/src/cac/: core/config.py, paths.py, campaign.py, coupling.py, references.py, boss.py, boss_candidates.py, boss_graph.py (if present), budget.py, search_index.py, and existing cli/common.py, cli/campaign.py, cli/boss.py, mcp/campaign.py, mcp/boss.py, cli/app.py, and mcp/server.py. Inspect corresponding tests and the packaged core/templates/docs/workflow.md. Use docs/boss-edition.md as the design reference. Resolve any actual filename differences with CodeGraph before changing code.
2. Implement domain logic in core/rumors.py, with configuration constants in core/config.py. Resolve owners through existing campaign reference/read interfaces, including archived owners, without requesting campaign-body mutability. Keep plain text separate from frontmatter serialization. Implement safe document paths, explicit existence errors, lazy creation, literal round trips, listing, and budgeted continuation reads. Validate before mutations and preserve existing bytes on failed input validation.
3. Add thin cli/rumors.py and mcp/rumors.py wrappers; register the CLI app and MCP tool module. Reuse body-file/editor conventions, confirmation adaptation, canonical identity reporting, pagination, and response-budget helpers as applicable. Define and document the get continuation contract in both interfaces; keep new domain logic in core. Do not change unrelated domains' truncation or input contracts.
4. Add focused tests in tests/core/test_rumors.py, tests/cli/test_rumors.py, and tests/mcp/test_rumors.py; extend tests/mcp/test_server.py registration coverage. Extend existing campaign/coupling and boss/reference/candidate tests where necessary to prove archive preservation and rumor exclusion. Review search_index.py enumeration and test that rumors are not accidentally indexed as bosses; adding a rumor search type, boss search, active-boss prime integration, and index-freshness redesign remain deferred.
5. Update core/templates/docs/workflow.md in the same change with the document model, commands/tools, ownership/reference behavior, terminal/archive exceptions, input/output and continuation contracts, and branch guidance. Update docs/boss-edition.md's implementation boundary and clarify the choices settled here. Broader world-planner/campaign-manager skill work, branching/migration guides, release numbering, and local instruction adoption remain later encounters. Do not edit deployed skills or run bootstrap.
6. Run focused verification, then repository quality checks. Preserve unrelated changes, including the existing modification to .agents/skills/campaign-manager/SKILL.md. Record any deviation from this locked plan through encounter messaging once reviewed/open.

## Verification

- Exercise core CRUD and list against temporary bootstrapped projects: missing storage, absent/duplicate documents, empty bodies, exact text round trips, independent campaigns, canonical/short refs, active fallback, no active campaign, missing and ambiguous owners, and archived owner resolution. Cover invalid names, traversal, link/junction handling where supported, and storage collisions; failed validation leaves existing content unchanged.
- Exercise CLI body/body-file/editor paths, mutual exclusion, UTF-8 failures, paths with spaces, multiline/YAML-looking/bracketed content, literal output, delete confirmation, and --yes. MCP tests cover equivalent results/errors and explicit required body arguments.
- Test list pagination and malformed/out-of-range cursors. Test oversized Unicode documents and continuation through CLI/MCP: bounded responses, explicit truncation/continuation information, complete reconstruction without lost or duplicated text, and no direct-file-read instruction for rumors.
- Verify rumors remain byte-identical and at the same live path through campaign completion, abandonment, reactivation, and archival, including coupled boss archival. After archival, read/update/delete through rumor operations still work while ordinary campaign/boss mutation guards remain intact. Test listing orphaned documents with clear diagnostics.
- Verify rumor presence/content never changes boss enumeration, candidate eligibility, numeric-reference allocation inputs, dependency lookup, or indexed boss results. No automatic boss creation, lineage, or status metadata.
- Verify CLI help and all five MCP tools are registered; review packaged workflow/design documentation against actual behavior. Branch expectations are guidance only; temporary projects require no Git branch to use endpoints.
- Run the narrow rumor and affected regression tests first, then `pdm run pytest -q`, `pdm run ruff check .`, and `pdm run ruff format .` with no remaining formatting changes. Fix failures without weakening tests or bypassing checks. No implementation checks are claimed by creation of this draft.

## Log

### Review - 2026-10-27T18:04:41Z - John Hoff

Independent review of scripted encounter e011-add-campaign-rumors against the world summary, assigned crypts-and-commits region, all five hydrated applicable lore bodies, and the cited rumors design finds no lore conflict. The plan provides CLI/MCP parity, literal output, thin wrappers over core logic, pagination and initial shared body truncation, registration coverage, same-change packaged workflow updates, deployed-skill preservation, and required full pytest/Ruff gates. The freeform document model, terminal/archive ownership behavior, boss exclusion, and branch-agnostic endpoints match the design. Implement and document the continuation contract in both interfaces, use markup=False for stored/user-originated CLI text, and complete the specified verification before claiming completion. PASS-WITH-NOTES; no flagged-but-unverified concerns.

### Message - 2026-10-27T18:06:13Z - John Hoff

Implementation clarification: rumors get returns bounded JSON with raw body text, a separate TRUNCATED notice, and hash-bound continuation cursors. The shared truncate_body helper embeds direct managed-file-read guidance and would contaminate chunk reconstruction, so this domain preserves the truncation/budget convention using a domain-specific serialized-envelope budget without changing other domains. CLI and MCP share the exact response. Stale cursors fail after document edits.

### Message - 2026-10-27T18:11:52Z - John Hoff

Implementation and verification finished. Added plain UTF-8 campaign rumors core storage, all five CLI/MCP document operations and registration, body-file/editor input, canonical/short campaign refs and active fallback, bounded JSON pagination and content-bound continuation reads, terminal/archived-owner editing, and orphan diagnostics. Regression tests cover literal round trips, validation/storage collisions, lifecycle/archive preservation including linked bosses, and exclusion from boss discovery/dependencies/index classification. Updated packaged workflow and design implementation boundary; tightened the new workflow text to preserve the existing docs response budget. Focused rumors/registration suite: 20 passed; documentation regressions: 6 passed; final full pytest: 1329 passed in 66.68s. Ruff check passed; ruff format reported 261 files unchanged. CLI rumors help and git diff --check passed. Existing unrelated deployed campaign-manager skill modification preserved. Encounter remains open awaiting the developer's explicit completion confirmation.

### Completed - 2026-10-27T18:12:39Z - John Hoff

Developer approved completion, commit, and push after verification: 1329 tests passed, Ruff lint clean, and formatting unchanged. Campaign rumors implemented and documented; implementation clarification and full verification evidence are recorded above.
