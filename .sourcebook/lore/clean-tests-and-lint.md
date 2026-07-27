---
assigned_regions: []
assigned_to_world: true
enabled: true
name: clean-tests-and-lint
summary: 'Gate before any encounter''s Verification is complete: `pdm run pytest -q`
  passes (no skips or deletions to dodge failures) and ruff is clean (`ruff check
  .` zero errors, `ruff format .` no diffs, fixes applied). A failing check is unfinished
  work - fix the cause before asking the user to confirm completion. Never use `--no-verify`,
  skip markers, or `# noqa` to route around a failure without explicit user approval.'
updated_by: John Hoff
updated_on: '2026-07-27T03:56:35Z'
---

# Clean Tests and Lint

Before an encounter's Verification is considered complete, both of the following must be true:

1. **Unit tests pass.** Run `pdm run pytest -q` from the repository root. Every test must pass - no skips added to dodge a failure, no test deleted or weakened just to make it green.
2. **Ruff is clean.** Run `pdm run ruff check .` with zero errors, and `pdm run ruff format .` with no remaining diffs. Formatting fixes are expected to be applied, not just reported.

If either check fails, treat it as unfinished work: fix the underlying cause before asking the user to confirm the encounter as `completed`. Do not use `--no-verify`, skip markers, or ruff `# noqa` suppressions to route around a failure unless the user explicitly approves the exception for that specific case.
