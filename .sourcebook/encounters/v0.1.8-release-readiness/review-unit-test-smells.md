---
archived: false
campaign: v0.1.8-release-readiness
created_by: John Hoff
created_on: '2026-08-05T02:51:26Z'
depends_on: []
name: review-unit-test-smells
regions:
- crypts-and-commits
status: draft
updated_by: John Hoff
updated_on: '2026-08-05T02:51:29Z'
---

# Encounter

## Requirements

- Audit `packages/crypts-and-commits/tests/` for the cause(s) of the test suite's currently long run time.
- Identify concrete "bad test smells" - at minimum: tests that are actually integration tests (touching the filesystem, subprocesses, or multiple `core` modules end-to-end) disguised as unit tests; duplicated or near-duplicated fixture setup that could be shared/parameterized instead; and any other unnecessary per-test overhead (e.g. redundant `cac bootstrap init`-equivalent setup, unnecessary sleeps/polling, over-broad fixture scope).
- Produce a concrete list of what was found, with file/test names, distinguishing "should be sped up in place" from "should be pulled out" (e.g. into a slower/optional suite, or reduced in scope).
- Any recommendation to actually split, mark, or restructure tests is scoped as a *recommendation* from this audit - implementing it is separate follow-up work, not automatically in scope here.

## Rationale

A slow unit test suite discourages running it frequently during development and in CI, and often signals that "unit" tests have quietly become integration tests (e.g. hitting real disk I/O per test rather than using shared/lighter fixtures). Before the project publishes a release, it's worth understanding why `pdm run pytest -q` is slow and whether the suite's current shape reflects deliberate integration coverage or just accumulated test smell - a bar `clean-tests-and-lint` lore already gates every encounter's Verification against, so it's a natural clean-up target ahead of a public release.

This encounter records the punchlist item as an audit; it's deliberately scoped to identify and report the problem, not to have pre-decided the restructuring approach before the investigation happens.

## Plan

Plan has not been described yet.

## Verification

Verification has not been described yet.
