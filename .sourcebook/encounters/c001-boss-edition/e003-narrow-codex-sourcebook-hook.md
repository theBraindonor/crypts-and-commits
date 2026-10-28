---
archived: false
campaign: c001-boss-edition
created_by: John Hoff
created_on: '2026-10-27T04:32:23Z'
depends_on:
- e001-finalize-boss-edition-design
kind: scripted
name: e003-narrow-codex-sourcebook-hook
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-10-27T04:48:04Z'
---

## Requirements

Implement the "Codex hook scope" design in `docs/boss-edition.md` for campaign `c001-boss-edition`.

Narrow the packaged Codex sourcebook guard to deny only `apply_patch` operations whose actual file targets modify managed sourcebook content. Check add, update, delete, and move/rename operations, including both the source and destination of a move. If any target in a multi-file patch is protected, deny the operation using the existing hook response shape and a clear reason.

Do not deny shell/Bash calls through this hook, even when their command text mentions the managed directory. Allow patches to ordinary files whose inserted, deleted, or context text mentions sourcebook paths. Match path components rather than substrings, so similarly named ordinary paths are not protected by accident. Handle relative paths, normalized dot segments, absolute paths, and Windows/POSIX separators as appropriate to the hook's supported payloads and platform. Preserve the distinction between actual patch headers and header-like strings inside patch content.

Update bootstrap registration to use an apply_patch-only matcher. Existing framework-owned broad registrations must be upgraded rather than left alongside a new registration. Preserve unrelated configuration and hook groups, including unrelated hooks sharing an old broad group. Re-running deployment must be idempotent and must not accumulate duplicate framework registrations.

Author changes only in packaged source and its deployment logic/tests. Do not edit, overwrite, disable, or redeploy this repository's live `.codex/config.toml`, `.codex/hooks/sourcebook_guard.py`, or deployed skills. The developer performs redeployment through `cac bootstrap init` and reviews/trusts the resulting hook via `/hooks` as applicable.

The MCP/CLI-only instruction for managed sourcebook content remains binding. Removing shell enforcement does not authorize direct shell content access. This is a narrower automated check, not a complete filesystem sandbox or a change to domain workflows, schema, permissions ownership, or Windows sandbox provisioning.

## Rationale

The current packaged hook searches the whole command string and is registered for both Bash and apply_patch. That can reject harmless shell operations and ordinary repository edits discussing sourcebook paths. Narrowing the check to actual patch targets reduces false positives while retaining protection against direct patch writes.

This is the campaign's third tentative item. Updating registration and its upgrade path in the same encounter is essential: changing the script alone would leave stale broad configuration in adopting projects. The Windows directory-ownership repair performed during e002 review was a separate sandbox issue and is not part of this hook change.

## Plan

1. Read `docs/boss-edition.md` ("Codex hook scope"), `CLAUDE.md`, and `AGENTS.md`. Work on the existing `c001-boss-edition` execution branch. Inspect the current implementation through CodeGraph before edits:
   - `packages/crypts-and-commits/src/cac/core/templates/codex/sourcebook_guard.py`.
   - `packages/crypts-and-commits/src/cac/core/bootstrap.py`, especially `initialize_codex_config` and `initialize_codex_guard_hook`.
   - `packages/crypts-and-commits/src/cac/cli/bootstrap.py`.
   - `packages/crypts-and-commits/tests/core/test_bootstrap.py` and `packages/crypts-and-commits/tests/cli/test_bootstrap.py`.
   Establish the actual supported hook event/payload shape and patch header syntax from the existing code/tests and available tool contract; preserve that contract. Document limits rather than claiming comprehensive sandbox enforcement.
2. In the packaged hook template, ignore non-apply_patch events and parse file-operation headers rather than searching the full patch text. Normalize target paths for the supported syntax/platform, include move destinations, and inspect all operations before deciding whether to deny. Keep incidental content references allowed. Keep the existing denial protocol; avoid unnecessary new dependencies or generic shell parsing. Define malformed/unsupported payload handling explicitly in tests and guidance without restoring whole-text false positives or claiming protection beyond the parsed contract.
3. In core bootstrap deployment configuration, register an apply_patch-only matcher and migrate recognized framework-owned legacy registrations. If an old group contains unrelated hooks, remove/move only the framework hook and preserve the unrelated group's matcher and contents. Preserve unrelated MCP settings and TOML formatting as supported by the existing implementation. Retain framework-owned hook-template replacement and idempotence. Adjust CLI bootstrap reporting only if needed to accurately describe the behavior. Bootstrap remains permanently CLI-only; no MCP operation is added.
4. Extend the existing core bootstrap tests to exercise the packaged/deployed-in-temp-directory hook with realistic synthetic events and the target-path matrix below. Add registration migration tests covering fresh configuration, an existing broad framework registration, shared groups with unrelated hooks, an already narrowed registration, repeated deployment, and preservation of unrelated settings. Update CLI bootstrap tests for deployment wiring and any reporting changes. These tests may invoke core bootstrap routines and exercise the CLI inside pytest temporary projects; the agent must never run bootstrap against the live repository.
5. Update `packages/crypts-and-commits/src/cac/core/templates/docs/workflow.md` in the same change to describe the actual hook scope, bootstrap upgrade behavior, unchanged MCP/CLI-only instruction, developer-only redeployment, and hook trust. Update `docs/QUICKSTART.md` to make the narrower enforcement and redeployment discoverable. Inspect `packages/crypts-and-commits/src/cac/core/templates/docs/migration-guide.md` for scope descriptions that need correction, preserving its existing migration approval/restore procedure. No skill procedure change is planned; if any necessary skill wording is discovered, author it only in the packaged `packages/crypts-and-commits/src/cac/core/templates/skills/{claude,codex}/` templates with matching workflow updates.
6. Leave repository-local `CLAUDE.md`/`AGENTS.md` adoption edits to the campaign's later adoption encounter; flag their old hook description in the handoff. Leave all deployed copies and live trust/guardrail settings unchanged. If the current live hook blocks legitimate template/test edits, report the precise blocker for developer resolution; do not disable it or use a different execution path to bypass it.
7. Run focused tests, full pytest, and Ruff checks; review the diff and record results through CAC. Hand off the developer redeployment/trust step separately from implementation verification. Obtain developer confirmation before marking the encounter complete.

## Verification

- Run `pdm run pytest packages/crypts-and-commits/tests/core/test_bootstrap.py packages/crypts-and-commits/tests/cli/test_bootstrap.py -q` first.
- Synthetic hook events must deny protected add/update/delete targets, move into or out of the managed directory, and a protected target later in a mixed multi-file patch. Cover supported relative/absolute paths, dot-segment normalization, Windows backslashes, POSIX separators, and platform-appropriate case handling.
- Allow ordinary-file patches containing managed paths in added/deleted/context text, including header-like text as content. Allow similarly named path components. Confirm non-apply_patch events, including shell calls mentioning managed content, yield no hook denial. These are synthetic fixtures, not actual direct sourcebook access.
- Verify the hook's event envelope, denial response, and documented malformed/unsupported input behavior. Tests should exercise the packaged template and deployment result, not the repository's live hook.
- Verify fresh and upgraded TOML registration uses only apply_patch for the framework hook, removes recognized stale broad registrations without dropping unrelated hooks, preserves unrelated settings, and remains idempotent after repeated deployment. Verify CLI bootstrap wiring and packaged template replacement in temporary projects.
- Verify docs distinguish the narrower hook from the continuing MCP/CLI-only instruction and developer-only deployment. No deployed artifacts, live settings, ownership/ACLs, or managed records are changed by implementation, apart from normal encounter tracking through CAC.
- Run `pdm run pytest -q`, `pdm run ruff check .`, and `pdm run ruff format .` from the repository root. Require passing tests and clean formatting/lint without weakening tests, skips, or suppressions to avoid failures. Preserve unrelated user changes.
- Run `git diff --check`, review the final diff, report results and any enforcement limitations, and request developer completion confirmation. Developer bootstrap/trust is a handoff step, never an agent-run verification command.

## Log

### Review - 2026-10-27T04:33:58Z - John Hoff

PASS-WITH-NOTES: Reviewed this scripted encounter against all five applicable lore bodies. The plan preserves bootstrap's CLI-only exception, confines framework changes to packaged source/templates, requires matching workflow documentation, leaves live deployed artifacts untouched, and includes the full pytest/Ruff completion gate. Target-path parsing and migration of legacy registrations are concrete and cover unrelated-hook preservation and idempotence. During implementation, establish the supported event/patch contract and document malformed-input limits; report any live-hook blocker without bypassing it. Preserve the handoff warning that local instruction adoption and developer redeployment/trust remain separate steps.

### Opened - 2026-10-27T04:34:30Z - John Hoff

Developer approved implementation following independent PASS-WITH-NOTES review.

### Message - 2026-10-27T04:35:20Z - John Hoff

Implementation opened with developer approval, but the existing live PreToolUse hook blocked the first required regression-test patch. Exact target: packages/crypts-and-commits/tests/core/test_bootstrap.py; intended change: replace shell-sourcebook-denial expectation with allow/no-output expectation. The context contains a synthetic Bash event with Get-Content .sourcebook/world.md, so the live whole-command regex denied this ordinary test-file edit. No source edit was applied. Per Plan step 6, stopped without disabling/redeploying the live hook or switching execution paths to bypass it. Developer must resolve the live-hook blocker before implementation can continue. Encounter remains open; verification has not begun.

### Message - 2026-10-27T04:41:51Z - John Hoff

Developer reported disabling the live CAC hook to resolve the recorded false-positive blocker; resumed without bypassing it or directly accessing managed content. Implemented packaged apply_patch-only guard with lexical add/update/delete/move target scanning, dot-segment and separator normalization, platform-aware case handling, multi-file checks, and literal-content allowance. Supported envelopes: tool_input string or tool_input.command string; malformed/unsupported inputs yield no decision, with explicit enforcement limits documented. Bootstrap upgrades recognized legacy broad registrations, preserves unrelated hooks/shared groups and custom settings, and deduplicates known registrations idempotently. Updated CLI reporting, workflow reference, migration guide, and Quickstart. Added/updated tests for target paths, content false positives, shell allowance, malformed envelopes, deployment upgrade, and template replacement in temporary projects. Verification: 93 focused bootstrap tests passed before final reporting adjustment; final full suite passed 985 tests; Ruff check clean; Ruff format left all 225 files unchanged; git diff --check clean; code/test/docs diffs reviewed. No live hook/config/skills/ACL edits or live bootstrap performed by agent. Developer must run pdm run cac bootstrap init from this repository and review/trust/re-enable the updated hook via /hooks. Local CLAUDE.md/AGENTS.md description adoption remains deferred to the campaign's adoption encounter. Implementation ready for completion confirmation; encounter stays open; changes uncommitted.

### Message - 2026-10-27T04:44:00Z - John Hoff

Developer reported running bootstrap and re-enabling the hook. Verified live .codex/config.toml registers ^apply_patch$ only, and deployed script text matches the packaged source after normal newline decoding. Exercised the live script with a synthetic protected-delete event: it returned the expected PreToolUse deny response without touching managed content. A real no-op patch to docs/QUICKSTART.md containing a sourcebook path reference was accepted, demonstrating the prior content false positive is resolved. Developer deployment/trust restoration is confirmed by report; agent did not alter deployed artifacts or trust settings. Implementation verification remains 985 tests passing and clean Ruff. Ready for explicit completion confirmation; encounter remains open and changes uncommitted.

### Completed - 2026-10-27T04:48:04Z - John Hoff

Completed with explicit developer confirmation. Implemented packaged apply_patch-only target checks, legacy registration migration/deduplication preserving unrelated hooks/settings, CLI reporting, regression tests, and matching workflow/migration/Quickstart guidance. Verification: 985 tests passed; Ruff clean; formatting and whitespace checks clean. Developer ran bootstrap, trusted/re-enabled the updated hook, and live verification confirmed the apply_patch-only matcher, deployed/source text equality, expected synthetic protected-target denial, and acceptance of an ordinary-file patch containing sourcebook references. Local agent-instruction adoption remains assigned to the later campaign adoption encounter. Changes are uncommitted.
