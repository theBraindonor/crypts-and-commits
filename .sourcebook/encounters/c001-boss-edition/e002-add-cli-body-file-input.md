---
archived: false
campaign: c001-boss-edition
created_by: John Hoff
created_on: '2026-10-27T03:58:22Z'
depends_on:
- e001-finalize-boss-edition-design
kind: scripted
name: e002-add-cli-body-file-input
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-10-27T04:26:53Z'
---

## Requirements

Implement the "CLI body files" contract in `docs/boss-edition.md` for all nine existing body-accepting commands:
- `world set-body`.
- `lore create` and `lore update`.
- `region create` and `region update`.
- `campaign create` and `campaign update`.
- `encounter create` and `encounter update`.

Add `--body-file PATH` as an alternative to `--body/-b`. Reject both options together with a clear CLI usage error, including when inline body is the empty string. Read files as UTF-8 without normalizing their newline characters at the input boundary. Pass the resulting text through the same core operations, validation, and lifecycle guards as inline input. Preserve existing core serialization/normalization behavior rather than changing stored-body semantics.

Handle missing paths, directories, read-permission/other file I/O failures, and invalid UTF-8 as actionable CLI errors without a traceback. Resolve file input before any record mutation; do not open an editor for explicitly supplied file input. Do not modify or delete the input file. An empty file is explicit empty input and follows existing inline empty-body behavior, never the omitted-input/editor path.

When neither body option is provided, preserve existing editor content, template selection (including encounter kind), required summaries, campaign resolution, and lifecycle handling. Preserve existing inline usage.

Resolve input through a shared CLI helper. Core and MCP continue accepting body strings; this is an input affordance on existing commands, not a new domain operation or a filesystem argument for MCP. Verify equivalent MCP operations already exist and keep their signatures, lifecycle behavior, response budgets, and output contracts unchanged.

Update CLI help, the packaged canonical workflow reference, and a public file-based usage example. No bosses/rumors commands exist yet; their future implementation encounters must use the same helper where they accept bodies. This encounter does not add those domains or change skills/hooks, branch behavior, or sourcebook schema.

## Rationale

Large markdown bodies are difficult to transmit reliably as shell arguments, particularly on Windows. File input avoids shell quoting and argument-length limits while keeping all managed writes inside the normal CAC core APIs. One shared helper prevents the nine commands from drifting on empty input, encoding, and error behavior.

This is the campaign's second tentative item, following the completed design encounter. The design contract is settled and independent of upcoming boss storage.

## Plan

1. Work on `c001-boss-edition`. Read `docs/boss-edition.md` ("CLI body files"), `CLAUDE.md`, and `AGENTS.md`. Inventory all `--body` options in `packages/crypts-and-commits/src/cac/cli/` to confirm the nine-command scope before editing.
2. In `packages/crypts-and-commits/src/cac/cli/common.py`, add a reusable body-input resolver that distinguishes absent input (None) from explicit empty text. Accept inline text and an optional file path, enforce mutual exclusion, read UTF-8 preserving input newlines, and translate encoding/I/O failures into clear CLI usage errors. Keep editor/template selection lazy and preserve command-specific behavior. Do not add filesystem reading to core or MCP.
3. Wire `--body-file` and the resolver into `cli/world.py`, `cli/lore.py`, `cli/region.py`, `cli/campaign.py`, and `cli/encounter.py` under `packages/crypts-and-commits/src/cac/`. Retain `--body/-b`, required summaries, active/explicit campaign resolution, encounter kind handling, and existing validation/lifecycle checks. Validate supplied input before any record write and prevent editor invocation on file-input errors. No requirement to change precedence among independent pre-existing validation errors.
4. Add focused helper tests in `packages/crypts-and-commits/tests/cli/test_common.py` and command integration/regression tests in the matching `test_world.py`, `test_lore.py`, `test_region.py`, `test_campaign.py`, and `test_encounter.py`. Parameterize the nine-command matrix where useful using the existing CLI fixtures; do not create a parallel test architecture. Cover successful core writes, unchanged input files, no writes/editor calls on input failure, explicit empty versus absent input, and preservation of summary/lifecycle/editor behavior. Test unreadable-file errors with a controlled I/O failure so the test does not depend on platform permissions.
5. Confirm matching body-string operations in `packages/crypts-and-commits/src/cac/mcp/{world,lore,region,campaign,encounter}.py`. Existing wrappers provide domain parity; local file input deliberately remains a CLI concern, so no MCP path parameter or new tool is needed. Retain existing literal body output; any diagnostics containing freeform user input/path text must avoid accidental Rich markup interpretation.
6. Update `packages/crypts-and-commits/src/cac/core/templates/docs/workflow.md` in the same change to document the additive input option, exclusivity, UTF-8/newline and empty-file behavior, error handling, editor fallback, and unchanged MCP body-text contract. Add a public example to `README.md`, using an ordinary input markdown file with a path containing spaces and explaining that CAC performs the managed write. CLI help should make the two input methods and fallback discoverable. Keep the design document consistent if implementation reveals an actual contract change; log any deviation through CAC before proceeding. No packaged skill procedure changes are required, and deployed skills/hooks must not be edited or redeployed by the agent.
7. Run the focused checks below, then the required full suite and Ruff checks. Inspect the diff for unrelated changes and confirm every existing `--body` command has `--body-file`. Record results and obtain developer confirmation before completing the encounter.

## Verification

- Run `pdm run pytest packages/crypts-and-commits/tests/cli/test_common.py packages/crypts-and-commits/tests/cli/test_world.py packages/crypts-and-commits/tests/cli/test_lore.py packages/crypts-and-commits/tests/cli/test_region.py packages/crypts-and-commits/tests/cli/test_campaign.py packages/crypts-and-commits/tests/cli/test_encounter.py -q` first.
- Across all nine commands, verify file bodies reach the ordinary core write with equivalent results to inline input and the input file remains byte-for-byte unchanged. Include multiline/large markdown, non-ASCII UTF-8, literal bracketed text, a path containing spaces, and LF/CRLF input. Check newline preservation at the resolver boundary separately from existing core storage semantics.
- Test mutual exclusion (including `--body ""`), empty files, missing files, directory paths, simulated unreadable files, and invalid UTF-8. Confirm nonzero usage errors, no traceback, no editor invocation on explicit file input/errors, and no record creation or mutation after failure.
- Check neither-option editor fallback and existing template/current-body content; inline empty input and file empty input must follow the same existing behavior. Preserve lore/region required summaries, encounter kind and draft-only update restrictions, campaign body locks, and active/explicit campaign handling.
- Inspect CLI help for every command and verify the workflow reference and public example match the implementation. Run existing relevant MCP regression tests (the corresponding files in `packages/crypts-and-commits/tests/mcp/`) if needed to investigate parity concerns; the full suite also covers MCP.
- Run `pdm run pytest -q`, `pdm run ruff check .`, and `pdm run ruff format .` from the repository root. Tests must pass and Ruff must be clean without skips, deleted/weakened tests, or suppressions to evade failures. Apply formatting fixes; preserve unrelated user changes and report scope conflicts before expanding the work.
- Check `git diff --check` and review the final diff. Report changes, verification results, and limitations; obtain developer confirmation before marking complete.

## Log

### Review - 2026-10-27T04:00:01Z - John Hoff

PASS-WITH-NOTES: Independently retrieved the encounter, world, assigned region, and all five applicable lore bodies through MCP. The scripted plan honors the test/lint gate, preserves CLI/MCP domain parity and response contracts, protects literal user content from Rich markup, avoids deployed skill edits and bootstrap, and updates the canonical workflow reference in the same change. Its nine-command scope, shared resolver, explicit-empty handling, input-before-mutation rule, and regression matrix are sufficiently concrete. Local tooling failures prevented independent inspection of repository instructions, the cited design, and implementation files, so existing command/MCP coverage and design correspondence remain unverified; no lore conflict was identified in the encounter itself.

### Message - 2026-10-27T04:04:46Z - John Hoff

Fresh independent re-review requested and authorized by the developer after CodeGraph initialization. This supersedes the earlier review's unresolved local-inspection limitation. Reviewer verdict and findings: PASS-WITH-NOTES: Independently retrieved the world, scripted encounter, assigned region, and all five applicable lore bodies through MCP, then inspected repository instructions, the world-manager skill, the cited CLI body-files design, current CLI source, and all corresponding MCP operations using CodeGraph and successful read-only shell calls. Confirmed exactly nine existing --body options and matching body-string MCP operations delegating to core. The plan honors test/lint gates, CLI/MCP parity, literal-content output, template-only skill authorship, and same-change canonical workflow documentation. Its empty-versus-absent distinction matches current CLI behavior, and its shared resolver and input-before-mutation contract match the design. Implementation caution: common.fail currently enables Rich markup, so file/path diagnostics must follow the plan's literal-safe requirement rather than pass raw paths through that helper unchanged. Earlier reader failures were recovered; no required inspection remains blocked. Runtime verification remains required during implementation. Encounter remains reviewed; no implementation has started.

### Message - 2026-10-27T04:18:46Z - John Hoff

Fresh independent review restarted at developer request after repairing repository .codex directory ownership. Reviewer returned: PASS-WITH-NOTES: Independently retrieved the world, scripted encounter, assigned region, and all five applicable lore bodies through MCP, then inspected the cited design and current CLI/MCP source. The plan honors test/lint gates, preserves domain parity through existing body-string MCP wrappers, requires literal-safe output, avoids deployed skill changes and bootstrap, and updates the canonical workflow reference in the same change. Confirmed nine existing body options and matching MCP operations. Implementation must avoid passing raw file-path diagnostics through the current markup-enabled common.fail helper. Runtime verification remains required during implementation; no lore conflict or review-blocking omission was identified. Tool-status confirmation: no sandbox, shell, Node, or CodeGraph execution failures and no escalated read workaround were required. Reviewer corrected one malformed JavaScript tool-call quoting error and completed narrower reads after output truncation; no required inspection remains incomplete. This review supersedes earlier local-tool limitations. Encounter remains reviewed; implementation has not begun.

### Opened - 2026-10-27T04:19:10Z - John Hoff

Developer approved implementation after the fresh independent review.

### Message - 2026-10-27T04:24:55Z - John Hoff

Implementation and verification complete, pending developer confirmation. Added shared cli.common.resolve_body_input and --body-file PATH to all nine existing body-accepting CLI commands. UTF-8 loading preserves input newlines, distinguishes explicit empty from absent input, rejects simultaneous inline/file input, reports I/O/decoding failures through literal-safe Typer usage errors, and leaves source files unchanged. Existing editor templates, summaries, active/explicit campaign handling, encounter kind, and lifecycle locks are preserved. Core and MCP signatures unchanged; checked matching body-string wrappers. Updated canonical packaged workflow reference and README example. Added 115 regression test cases, including nine-command success/error/editor/help matrices, large and bracketed Unicode bodies, newline checks, and lifecycle/summary guards. Verification: 315 focused CLI tests passed; full suite 925 passed; Ruff check passed; Ruff format left all 224 files unchanged on final run; git diff --check passed; final code/docs/test diffs reviewed. No plan deviation, deployed artifact edits, schema changes, or new domain operations. Unrelated untracked .codegraph and .claude/settings.local.json preserved. Encounter remains open until explicit completion confirmation; no commit or push performed.

### Completed - 2026-10-27T04:26:53Z - John Hoff

Completed with explicit developer confirmation. Implemented --body-file PATH across all nine existing body-accepting CLI commands with shared UTF-8/newline-preserving input resolution, explicit-empty handling, mutually exclusive options, and literal-safe usage errors before writes. Preserved editor, summary, kind, campaign resolution, and lifecycle behavior; core/MCP body-string APIs unchanged. Updated README and canonical workflow reference. Verification: 315 focused CLI tests passed; all 925 tests passed; Ruff check clean; Ruff format left 224 files unchanged; git diff --check clean. Implementation and encounter records remain uncommitted.
