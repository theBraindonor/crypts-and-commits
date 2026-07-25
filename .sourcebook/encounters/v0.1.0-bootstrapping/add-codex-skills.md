---
campaign: v0.1.0-bootstrapping
created_by: John Hoff
created_on: '2026-07-25T03:15:45Z'
name: add-codex-skills
regions: []
status: completed
updated_by: John Hoff
updated_on: '2026-07-25T03:29:15Z'
---

# Requirements



- Add Codex-discoverable copies of the existing `world-manager` and `campaign-manager` skills under `.agents/skills/`.

- Adapt Claude-specific metadata and tool terminology for Codex while preserving CAC lifecycle behavior and the `.sourcebook/` CLI-only guardrail.

- Update root `AGENTS.md` to reference the Codex skill locations and portable CAC command behavior.

- Leave packaged template/bootstrap support for a later encounter.



# Rationale



Codex scans repository-local skills from `.agents/skills`, while the current skills are only available under `.claude/skills`. Providing native Codex copies enables immediate dogfooding without prematurely implementing the planned template deployment feature.



# Plan



1. Copy both existing skill definitions into matching directories under `.agents/skills/`.

2. Remove Claude-only `allowed-tools` frontmatter and translate `Bash`/`Task` instructions to Codex-equivalent shell and subagent workflows.

3. Document portable `cac` invocation, using `pdm run cac` in this development repository.

4. Update `AGENTS.md` to point Codex at the new skills and remove the temporary `.claude/skills` compatibility routing.

5. Validate both skill files with deterministic PowerShell checks for required frontmatter, expected names, and absence of Claude-only declarations or tool names.



# Verification



- Confirm `.agents/skills/world-manager/SKILL.md` and `.agents/skills/campaign-manager/SKILL.md` exist.

- Parse each YAML frontmatter block and confirm it contains the expected `name` plus a non-empty `description`.

- Search the Codex copies and confirm they contain none of `allowed-tools`, `Bash(`, the `Task` tool, or `subagent_type`.

- Confirm `AGENTS.md` references `.agents/skills` and preserves the `.sourcebook/` and bootstrap guardrails.

- Run `pdm run pytest -q` and fix every failure without skips or weakened tests.

- Run `pdm run ruff check .` and fix every error without suppression bypasses.

- Run `pdm run ruff format .`, apply any formatting changes, then run `pdm run ruff format . --check` to confirm no formatting drift remains.

## Log

### Review - 2026-07-25T03:20:35Z - John Hoff

PASS-WITH-NOTES: The Plan honors the applicable clean-tests-and-lint lore by requiring the full pytest and Ruff test/check/format gates and prohibiting skips, weakened tests, and suppression bypasses. The encounter is reviewable and lore-consistent. Note that the proposed deterministic checks verify metadata and removal of Claude-only terminology but do not positively establish preservation of CAC lifecycle behavior, particularly the independent reviewer workflow, or every sourcebook guardrail; implementation should compare the adapted skill content closely or add focused assertions for those requirements.

### Opened - 2026-07-25T03:21:20Z - John Hoff

User approved implementation.

### Message - 2026-07-25T03:24:59Z - John Hoff

Implementation completed. Codex resolved the user-scoped PDM executable after sandbox read grants, but sandboxed execution still exited silently, so CAC and verification commands were run through the approved absolute PDM path. Structural checks passed; pytest: 465 passed; ruff check: clean; ruff format: 51 files unchanged and check passed.

### Completed - 2026-07-25T03:29:15Z - John Hoff

User confirmed completion after durable PDM command approval was established; previously recorded verification passed (465 tests, Ruff check clean, Ruff formatting unchanged).
