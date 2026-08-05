---
archived: true
campaign: v0.1.3-skill-and-configuration-bundling
created_by: John Hoff
created_on: '2026-07-28T00:41:22Z'
depends_on: []
name: template-and-deploy-agent-skills
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-08-04T06:47:13Z'
---

# Template And Deploy Agent Skills

## Requirements

- `world-manager` and `campaign-manager` skill content becomes packaged, importable template data (ships inside the wheel via `importlib.resources`), not just loose files under this repo's `.claude/skills/` and `.agents/skills/`.
- `cac bootstrap init` deploys both skills, in both flavors (Claude Code and Codex), into a target project's `.claude/skills/<name>/SKILL.md` and `.agents/skills/<name>/SKILL.md`.
- The `.sourcebook/**` Edit-deny rule in `.claude/settings.json` is already handled by `initialize_claude_settings` (shipped in v0.1.1-mcp-transition) — no new work needed there. This encounter is scoped to the skill files only.

## Rationale

- Mirrors `world.md`'s existing pattern: `core/templates/skills/` as a packaged sibling of `core/templates/sourcebook/`.
- Unlike `world.md`, skill content needs no per-project stamping (no `created_by`/`created_on`) — it's a straight file copy, seeded from this repo's current `.claude/skills/` and `.agents/skills/` files verbatim. The two flavors are genuinely different files (Codex's lacks `allowed-tools` frontmatter, has an extra "Command execution" section, and uses bare tool names instead of `mcp__`-prefixed ones) — not one source template with variants generated at bootstrap time.
- Deploy semantics: unconditional overwrite on every `cac bootstrap init` run, not create-if-missing like `initialize_world`. This is a deliberate departure from the `.sourcebook/` content pattern: skill files are framework-owned, not user-editable data, so when the packaged skill content is updated in a new `cac` release, re-running `bootstrap init` against an existing project must propagate that update rather than leaving the stale deployed copy in place. The explicit tradeoff, confirmed with the user: any local hand-edit to a deployed skill file is lost on the next `bootstrap init`. This is closer in spirit to `initialize_claude_settings`/`initialize_mcp_config` (which reconcile toward a desired state on every run) than to `initialize_world`, but simpler — a full-file overwrite, since there's no user-editable surface within a skill file worth merging around.

## Plan

1. Add `core/templates/skills/{claude,codex}/{world-manager,campaign-manager}/SKILL.md`, seeded from the current repo files under `.claude/skills/` and `.agents/skills/` respectively (copied verbatim, no content changes).
2. Extend `cac.core.templates.load()` (or add a sibling helper) to handle the extra path nesting under `templates/skills/` — unlike the flat `templates/sourcebook/` package, this is two directories deep (flavor/skill-name).
3. Add `core/skills.py` with `deploy_skills(root: Path) -> list[tuple[Path, bool]]` that writes each packaged skill file unconditionally to its target path under `root`, creating parent directories as needed, and returns `(path, changed)` per file — `changed` reflects whether the write actually altered content (byte comparison against any existing file), the same "did this run do anything" signal `initialize_claude_settings` reports, just for full-file overwrite instead of merge.
4. Wire `deploy_skills` into `cli/bootstrap.py`'s `init` command, after the existing steps, reporting each deployed file the same way `world.md` creation is reported today (created / already up to date, styled consistently with the existing `_report*` helpers).
5. Tests:
   - `tests/core/test_skills.py`: all 4 files are created on a fresh root; a second run with no source changes reports `changed=False` for each; a locally-modified deployed file is overwritten back to the packaged content (`changed=True`) on the next call.
   - `tests/cli/test_bootstrap.py`: extend the existing `cac bootstrap init` CLI test(s) to assert all 4 skill files exist with expected content after a run.
6. Do not touch this repo's own `.claude/skills/` or `.agents/skills/` — they remain the working source-of-truth copies (per CLAUDE.md's "Agent skills" section); this encounter only adds the packaging + deployment mechanism, seeded from their current content.

## Verification

- `pdm run pytest -q` passes, including the new tests.
- `pdm run ruff check .` is clean (zero errors) and `pdm run ruff format .` reports no diffs (per the `clean-tests-and-lint` world lore).
- Manually run `cac bootstrap init` (via `pdm run cac bootstrap init`) against a scratch temp directory and confirm `.claude/skills/world-manager/SKILL.md`, `.claude/skills/campaign-manager/SKILL.md`, `.agents/skills/world-manager/SKILL.md`, and `.agents/skills/campaign-manager/SKILL.md` are created with content matching this repo's current skill files.

## Log

### Review - 2026-07-28T00:45:02Z - John Hoff

Plan checked against all three applicable lore items and holds up: Verification correctly gates on `pdm run pytest -q` plus clean ruff check/format (clean-tests-and-lint); the new `deploy_skills` mechanism stays entirely within the `bootstrap init`-is-CLI-only exception so no MCP-parity gap is introduced (cli-mcp-parity), confirmed against the actual `cli/bootstrap.py`, which already reports each init step via the same `_report*`-style CLI-authored markup strings the Plan proposes to reuse — no stored body content is printed, so console-best-practices' markup=False rule isn't implicated (console-best-practices). One non-lore note for GM awareness: CLAUDE.md's 'Agent skills' section still describes this exact migration as something to defer until the skills are 'fully bootstrapped and working... not a current task,' and the Plan doesn't propose updating that wording post-completion — worth an explicit go-ahead that the precondition is now considered met.

### Completed - 2026-07-28T01:44:32Z - John Hoff

Implemented core/templates/skills/{claude,codex}/{world_manager,campaign_manager}/SKILL.md (seeded byte-identical from .claude/skills/ and .agents/skills/), core/skills.py::deploy_skills() with unconditional overwrite semantics, and wiring into cli/bootstrap.py init. pdm run pytest -q: 677 passed. ruff check . and ruff format . --check: clean. Manually verified cac bootstrap init against a scratch temp dir deploys all 4 skill files with content matching source (aside from platform-default CRLF line endings, consistent with the rest of the codebase's write_text calls).
