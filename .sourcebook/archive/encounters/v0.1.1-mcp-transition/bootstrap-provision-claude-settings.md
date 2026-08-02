---
archived: true
campaign: v0.1.1-mcp-transition
created_by: John Hoff
created_on: '2026-07-25T20:58:13Z'
depends_on: []
name: bootstrap-provision-claude-settings
regions: []
status: completed
updated_by: John Hoff
updated_on: '2026-08-02T22:11:30Z'
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
  - `permissions.allow`: `"mcp__crypts-and-commits"`, so the MCP server's tools
    are usable immediately without a first-use permission prompt (matches this
    repo's existing entry, and should be derived from the existing
    `MCP_SERVER_NAME` constant in `core/config.py` rather than hardcoded again).
  - top-level `enabledMcpjsonServers: ["crypts-and-commits"]`, so the `.mcp.json`
    entry that `initialize_mcp_config` already writes (under the same
    `MCP_SERVER_NAME`) is trusted automatically. In this repo that key
    currently only lives in the gitignored `.claude/settings.local.json`, not
    the checked-in `settings.json` — for a freshly bootstrapped project it
    needs to be in the CLI-provisioned file so MCP access works out of the box.
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
   `MCP_CONFIG_FILE_NAME` / `mcp_config_path`. Reuse the existing
   `MCP_SERVER_NAME` constant (already `"crypts-and-commits"`) for both the
   `permissions.allow` entry (as `f"mcp__{MCP_SERVER_NAME}"`) and the
   `enabledMcpjsonServers` entry — do not hardcode the server name a second
   time.
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
   `enabledMcpjsonServers: ["crypts-and-commits"]`), either by re-running
   bootstrap against this repo or by hand to match what the command now
   produces.
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
  `.claude/settings.json` matches the intended shape (allow
  `mcp__crypts-and-commits`, deny both `Edit(.sourcebook/**)` and
  `Write(.sourcebook/**)`, `enabledMcpjsonServers: ["crypts-and-commits"]`).

## Log

### Review - 2026-07-25T22:11:46Z - John Hoff

Reviewed against the world's applicable lore set (clean-tests-and-lint is the only item in scope, since this encounter carries no region assignment); the Plan explicitly gates its Verification on `pdm run pytest -q` and clean `ruff check`/`ruff format`, satisfying it directly. Cross-checked the Plan's technical claims against the actual source (core/config.py, core/paths.py, core/bootstrap.py, cli/bootstrap.py) and the current .claude/settings.json/.claude/settings.local.json, and every cited existing pattern (MCP_SERVER_NAME, MCP_CONFIG_FILE_NAME, mcp_config_path, initialize_mcp_config's load/merge/write-back shape, the _report/_report_mcp_config reporting convention, and the current settings files' actual contents) is accurate, not assumed. One open question noted but not investigated further per review scope: the encounter has no region assignment, so region-level lore (if any exists for core/cli conventions) was never in scope for this check — worth a second look before or during implementation, not a blocker to reviewing as drafted.

### Message - 2026-07-25T22:20:04Z - John Hoff

Deviation from the drafted Requirements/Plan, found during implementation: the drafted Requirements called for `permissions.deny` to include both `Edit(.sourcebook/**)` and `Write(.sourcebook/**)`. Verified against Claude Code's actual permission-rule semantics (via the claude-code-guide agent, citing the permissions documentation): file-permission checks only match `Edit(path)`/`Read(path)` rules — a `Write(path)` rule is accepted in settings.json but never enforced and triggers a startup warning, and `Edit(path)` rules already cover all file-editing tools including `Write`. So the earlier premise (carried over from CLAUDE.md's own pre-existing, likewise-mistaken text) was itself a hallucination that had not been fully corrected. Implemented `initialize_claude_settings` to add only `Edit(.sourcebook/**)` to `permissions.deny` (plus the `permissions.allow` and `enabledMcpjsonServers` entries as specified), updated this repo's own `.claude/settings.json` to match, and corrected CLAUDE.md's guardrail section to state the real semantics instead of the false Edit+Write claim. Verification's manual-check wording ("deny both Edit(...) and Write(...)") is superseded by this: the correct, actually-enforced shape denies only Edit(.sourcebook/**).

### Completed - 2026-07-25T22:20:50Z - John Hoff

Shipped: initialize_claude_settings() in core/bootstrap.py provisions .claude/settings.json (permissions.allow mcp__crypts-and-commits, permissions.deny Edit(.sourcebook/**), enabledMcpjsonServers crypts-and-commits), wired into cac bootstrap init, with this repo's own settings.json and CLAUDE.md brought in line. Mid-implementation correction: dropped the drafted Write(.sourcebook/**) deny rule after confirming it's not an enforced Claude Code permission form (Edit already covers Write) — see the prior log message. pdm run pytest -q (568 passed), ruff check/format clean, and a manual scratch-directory bootstrap run all verified.
