---
archived: true
campaign: v0.1.1-mcp-transition
created_by: John Hoff
created_on: '2026-07-25T22:46:51Z'
depends_on: []
name: bootstrap-provision-codex-config
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-08-02T22:11:30Z'
---

# Encounter

## Requirements

- `cac bootstrap init` must create, or merge into an existing, `.codex/config.toml` at the bootstrapped project root. It must never replace the document wholesale merely to register CAC.
- The resulting TOML must configure the Codex MCP server at `[mcp_servers.crypts-and-commits]` with:
  - `command` set to the installed `cac-mcp` executable resolved by the existing `resolve_cac_mcp_executable()` helper;
  - `args = []`; and
  - `default_tools_approval_mode = "approve"`.
- Preserve unrelated top-level keys, tables, comments/formatting where supported by the chosen TOML document library, and every other MCP-server entry. Re-running bootstrap must be idempotent: it must not duplicate the server table or otherwise change an already compliant configuration.
- If the CAC server table already exists, merge/correct the required CAC settings in that table without discarding unrelated keys in it.
- Use a TOML parser/writer that can round-trip and mutate a document safely; add its runtime dependency and lockfile update if needed. Do not implement an ad-hoc TOML serializer.
- Add a core bootstrap helper plus path/config constants, and invoke it from the existing `cli/bootstrap.py` `init` command. The CLI must report whether the Codex config was created/updated or was already compliant, following the existing MCP and Claude-settings reporting style.
- `bootstrap` remains deliberately CLI-only; no MCP tool is added for this work.

## Rationale

CAC's bootstrap command already provisions `.mcp.json` for generic MCP clients and
`.claude/settings.json` for Claude Code. Codex needs its separate
`.codex/config.toml` registration and approval setting before it can use the
`crypts-and-commits` MCP server without per-call approval. The project's newly
created local configuration establishes the intended table and values; folding
that behavior into bootstrap makes it available to every newly bootstrapped
project while respecting users' existing Codex configuration.

## Plan

1. Add constants and a `codex_config_path(root)` helper for
   `.codex/config.toml`, alongside the existing bootstrap configuration paths.
   Reuse `MCP_SERVER_NAME` and `resolve_cac_mcp_executable()`; do not
   duplicate the server name or platform-specific executable-resolution logic.
2. Add a TOML document dependency capable of parsing, editing, and serializing
   existing TOML without an ad-hoc writer. Update the package metadata and lock
   state as required.
3. Implement `initialize_codex_config(root: Path) -> tuple[Path, bool]` in
   `core/bootstrap.py`: create the parent directory, parse an existing file or
   begin a document, create/navigate `mcp_servers` and the
   `crypts-and-commits` table, merge the three required values, preserve
   unrelated values, and write only when the document changed.
4. Wire the helper into `cac bootstrap init` and add a focused reporting helper
   that identifies `.codex/config.toml` and distinguishes updated from
   already-configured results.
5. Add core and CLI tests covering a new file, a config containing unrelated
   top-level configuration and another MCP server, an existing CAC table with
   unrelated keys, correction of stale required values, and an idempotent
   second run. Assert the generated TOML can be parsed and has the exact
   required values.
6. Update bootstrap-facing documentation only where it currently enumerates
   provisioned configuration files, so it explains that Codex configuration is
   merged rather than overwritten.

## Verification

- Focused core and CLI bootstrap tests pass, including TOML round-trip/merge and
  idempotency cases.
- `pdm run pytest -q` passes.
- `pdm run ruff check .` reports no errors and `pdm run ruff format .` leaves
  no diffs.
- In a scratch project containing a pre-existing `.codex/config.toml` with
  unrelated values, run `cac bootstrap init`; confirm those values remain and
  the `[mcp_servers.crypts-and-commits]` table contains the resolved
  `cac-mcp` command, empty arguments, and `default_tools_approval_mode =
  "approve"`. Run it again and confirm no additional change is made.

## Log

### Review - 2026-07-25T22:48:11Z - John Hoff

PASS-WITH-NOTES: The plan conforms to all applicable lore. Its full pytest and Ruff verification satisfies clean-tests-and-lint without proposing bypasses; the CLI change is limited to the explicitly exempt, developer-only bootstrap command and correctly adds no MCP tool; and its new reporting is CLI-authored status output rather than stored/free-form content, so the console markup rule is not implicated. No lore-relevant concerns were flagged as unverified.

### Opened - 2026-07-25T22:49:33Z - John Hoff

Approved by the developer to proceed with implementation.

### Completed - 2026-07-25T22:54:23Z - John Hoff

Implemented Codex bootstrap configuration provisioning: .codex/config.toml is created or merged with the crypts-and-commits MCP server, resolved cac-mcp command, empty args, and automatic tool approval while preserving unrelated TOML. Added tomlkit plus focused core/CLI coverage. Verified with 573 passing tests, Ruff check, and Ruff format check.
