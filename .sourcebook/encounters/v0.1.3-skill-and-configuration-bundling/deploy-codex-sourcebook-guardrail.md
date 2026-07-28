---
campaign: v0.1.3-skill-and-configuration-bundling
created_by: John Hoff
created_on: '2026-07-28T01:56:45Z'
depends_on: []
name: deploy-codex-sourcebook-guardrail
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-07-28T02:12:33Z'
---

## Requirements

- Extend `cac bootstrap init` so a bootstrapped target project receives a Codex-native `.sourcebook` filesystem guardrail alongside the existing Claude Code guardrail and agent-skill deployment.
- Deploy the guardrail as a project-local Codex `PreToolUse` hook and its executable support file(s) under the target project's `.codex/` directory.
- Configure the hook to reject direct filesystem edits to `.sourcebook/` made through Codex shell and patch/edit tools, while allowing the `crypts-and-commits` MCP server and `cac` CLI fallback to continue managing the sourcebook.
- Package Codex configuration and hook templates with the CAC distribution and load them through `importlib.resources`, so wheel installations can deploy them without relying on repository-relative source files.
- Preserve a target project's existing `.codex/config.toml` content when adding the hook configuration; bootstrap must be idempotent and must not duplicate hook registration or overwrite unrelated Codex settings.
- Support the operating systems supported by the CAC CLI, including a valid Windows hook command.
- Keep the existing `.claude/settings.json` behavior intact.
- Update relevant documentation and bootstrap tests to describe and verify the Codex deployment.

## Rationale

CAC's sourcebook is intentionally managed through its MCP server or CLI, not by direct file edits. Bootstrap already establishes this guardrail for Claude Code, but Codex users currently receive only instruction-level guidance. Codex hooks provide the closest supported, project-local pre-execution guardrail: they can inspect and deny shell and patch operations before they run. Deploying this configuration from bootstrap keeps a target project's Claude and Codex setup aligned and removes manual setup from each project.

This is a guardrail, not an OS-level security boundary. The implementation must state that limitation accurately and must not block the approved CAC MCP/CLI interfaces.

## Plan

1. Inspect the current bootstrap implementation, packaged-template layout, and bootstrap tests to identify the appropriate `importlib.resources` template package and merge points for target-project `.codex` assets.
2. Add packaged Codex templates in the CAC template package: a deterministic sourcebook-guard hook plus the configuration needed to register it for `PreToolUse` on shell and patch/edit calls. Design the hook to emit Codex's documented deny response and to recognize direct `.sourcebook` path references.
3. Extend bootstrap to load those templates through `importlib.resources` and create or merge the target project's `.codex` configuration and hook files without clobbering unrelated content; make repeated bootstrap runs stable.
4. Add focused tests for fresh deployment, wheel/package-resource loading where practical, merging with existing Codex configuration, idempotency, and preservation of the Claude guardrail. Cover the hook's allow/deny behavior directly where practical.
5. Update user-facing bootstrap and guardrail documentation to explain the Codex hook, its required trust/enablement behavior, and its non-security-boundary limitation.
6. Run the focused bootstrap and hook tests, then the repository's required test and Ruff checks.

## Verification

- Bootstrap tests demonstrate that a new target project receives the expected `.codex` hook assets and configuration from packaged resources.
- Tests demonstrate that pre-existing `.codex/config.toml` settings survive deployment and a second bootstrap invocation does not duplicate or change deployed entries.
- Hook tests show direct `.sourcebook` shell/patch references produce a Codex deny response, while unrelated commands and CAC's intended MCP/CLI path remain unblocked.
- Existing Claude settings deployment remains covered and passing.
- `pdm run pytest -q` passes.
- `pdm run ruff check .` reports no errors, then `pdm run ruff format .` is run to apply required formatting; a final `pdm run ruff format . --check` reports no remaining formatting changes.

## Log

### Review - 2026-07-28T02:00:24Z - John Hoff

The Plan honors `clean-tests-and-lint` by requiring the full pytest and Ruff gate, honors `cli-mcp-parity` because `bootstrap init` is explicitly CLI-only, and does not implicate `console-best-practices` unless new CLI output is added (which must then use `markup=False` for stored/free-form text). Codex hook protocol details, trust/enablement behavior, and Windows-command validity are flagged but unverified because the Plan cites no reviewable local source for them; this is a note rather than a lore conflict.

### Message - 2026-07-28T02:04:07Z - John Hoff

Design clarification from the developer: direct reads of `.sourcebook` are acceptable; the Codex guardrail should block direct edits only. Do not register only `apply_patch`, because that would leave direct shell edits unguarded. Keep interception for both `apply_patch` and Bash, but have the Bash policy distinguish write-capable operations from reads (for example, allow `Get-Content` while denying `Set-Content`, redirection, deletion, moves, and other direct modifications).

### Opened - 2026-07-28T02:05:52Z - John Hoff

Developer approved implementation with the current stricter hook pattern; revisit and relax the shell policy only if a genuine need arises.

### Completed - 2026-07-28T02:12:33Z - John Hoff

Implemented and verified Codex sourcebook guardrail deployment. Bootstrap now deploys a packaged PreToolUse hook and merges its registration into project-local Codex configuration; focused tests, the full pytest suite, Ruff check, and Ruff format check all pass.
