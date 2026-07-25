# Codex repository instructions

## Shared project guidance

Before doing any work in this repository, read `CLAUDE.md` in full and treat it as
the shared repository instructions. This directive is the Codex equivalent of an
import; Codex does not currently support a native include directive in
`AGENTS.md`.

If guidance in this file conflicts with `CLAUDE.md`, this file takes precedence
for Codex.

## Codex-specific overrides

- Translate references to Claude Code tools into the equivalent Codex tools and
  workflows. Tool names in `CLAUDE.md` describe intent, not a requirement to use
  a Claude-specific interface.
- The Codex-native `world-manager` and `campaign-manager` skills live under
  `.agents/skills/` and are auto-discovered by Codex. When `CLAUDE.md` requires
  either workflow, use the corresponding skill:
  - `.agents/skills/world-manager/SKILL.md`
  - `.agents/skills/campaign-manager/SKILL.md`
- Prefer the `cac` MCP server's tools (registered as `cac` per `.mcp.json`) as
  the primary interface for `.sourcebook` work; shell out to the `cac` CLI only
  when the MCP server isn't connected for the session. Skill examples show both
  forms — MCP tool first, `cac ...` CLI fallback second. In this development
  repository, run CLI fallback commands as `pdm run cac ...`.
- Preserve the `.sourcebook/` MCP/CLI-only guardrail. Never inspect or mutate
  its contents directly, and never run `cac bootstrap init` — `bootstrap` is
  also never exposed over MCP, by design.
- Use `apply_patch` for manual file edits. Preserve unrelated user changes in a
  dirty worktree.
- Verify changes with the narrowest relevant tests first, then run broader
  checks when warranted. The canonical test, lint, and format commands remain
  those documented in `CLAUDE.md`.
