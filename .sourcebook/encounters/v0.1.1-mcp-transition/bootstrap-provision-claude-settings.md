---
campaign: v0.1.1-mcp-transition
created_by: John Hoff
created_on: '2026-07-25T20:58:13Z'
depends_on: []
name: bootstrap-provision-claude-settings
regions: []
status: draft
updated_by: John Hoff
updated_on: '2026-07-25T20:58:13Z'
---

# Encounter

## Requirements

- `cac bootstrap init` must create, or merge into an existing, `.claude/settings.json`
  at the project root — mirroring how `initialize_mcp_config` already handles
  `.mcp.json` (load if present, otherwise start empty; preserve unrelated existing
  keys; write back).
- The provisioned settings must include:
  - `permissions.deny`: `"Edit(.sourcebook/**)"` and `"Write(.sourcebook/**)"`.
    CLAUDE.md's guardrail describes both Edit and Write as denied, but this
    repo's own hand-authored `.claude/settings.json` currently only lists the
    Edit rule — the new command should provision both, and this repo's file
    should be brought in line rather than treated as the reference to copy
    verbatim.
  - `permissions.allow`: `"mcp__cac"`, so the cac MCP server's tools are usable
    immediately without a first-use permission prompt (matches this repo's
    existing entry).
  - top-level `enabledMcpjsonServers: ["cac"]`, so the `.mcp.json` cac entry
    that `initialize_mcp_config` already writes is trusted automatically. In
    this repo that key currently only lives in the gitignored
    `.claude/settings.local.json`, not the checked-in `settings.json` — for a
    freshly bootstrapped project it needs to be in the CLI-provisioned file so
    MCP access works out of the box.
- Merging must be additive and idempotent: dedupe within the `permissions.allow`
  / `permissions.deny` lists and within `enabledMcpjsonServers` (only add an
  entry if not already present), never overwrite a developer's own unrelated
  permissions or duplicate entries on repeated runs.
- The CLI must report whether the file was newly created, changed, or already
  up to date, consistent with the existing `_report` / `_report_mcp_config`
  pattern in `cli/bootstrap.py`.

## Rationale

CLAUDE.md already flags this as a known gap: "`cac bootstrap init` should
provision (create, or merge into an existing) `.claude/settings.json` with
this same `.sourcebook/**` Edit/Write deny rule ... rather than that guardrail
having to be set up by hand as it was in this repo. Not yet implemented."
Closing it means every newly bootstrapped project automatically gets the same
`.sourcebook/**` protection and immediate MCP access this repo currently has
only because it was configured by hand, one project at a time.

## Plan

1. Add a settings-file-name constant (e.g. `CLAUDE_SETTINGS_FILE_NAME =
   ".claude/settings.json"`) to `core/config.py`, and a
   `claude_settings_path(root)` helper to `core/paths.py`, mirroring
   `MCP_CONFIG_FILE_NAME` / `mcp_config_path`.
2. Add `initialize_claude_settings(root: Path) -> tuple[Path, bool]` to
   `core/bootstrap.py`: load the existing JSON if present (else `{}`), merge in
   the required `permissions.allow` entry, the two `permissions.deny` entries,
   and the `enabledMcpjsonServers` entry — each added only if not already
   present, preserving every other existing key and list entry untouched —
   then write back with the same `json.dumps(..., indent=2) + "\n"` formatting
   `initialize_mcp_config` uses. Return the path and whether anything changed.
3. Wire the new step into `cli/bootstrap.py`'s `init()` command alongside the
   existing three steps, with its own `_report_claude_settings` helper for
   created / changed / already-up-to-date output, following the existing
   `_report` / `_report_mcp_config` shape.
4. Bring this repo's own `.claude/settings.json` in line with the new output
   (add the missing `Write(.sourcebook/**)` deny entry and
   `enabledMcpjsonServers: ["cac"]`), either by re-running bootstrap against
   this repo or by hand to match what the command now produces.
5. Update CLAUDE.md's bootstrap-guardrail section to remove the "Not yet
   implemented" note once this ships.

## Verification

- New unit tests in `tests/core/test_bootstrap.py` for
  `initialize_claude_settings`: fresh-file creation, merging into an existing
  file with unrelated keys/entries preserved, and idempotent re-run (no
  duplicate list entries, `changed=False` on the second call).
- New/updated tests in `tests/cli/test_bootstrap.py` covering `init`'s new
  reporting output.
- `pdm run pytest -q` passes; `pdm run ruff check .` and `pdm run ruff format
  .` are clean, per the `clean-tests-and-lint` world lore.
- Manually run bootstrap against a scratch directory and confirm the resulting
  `.claude/settings.json` matches the intended shape (allow `mcp__cac`, deny
  both `Edit(.sourcebook/**)` and `Write(.sourcebook/**)`,
  `enabledMcpjsonServers: ["cac"]`).
