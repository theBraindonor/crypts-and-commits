---
assigned_regions:
- crypts-and-commits
assigned_to_world: false
created_by: John Hoff
created_on: '2026-07-28T03:52:47Z'
enabled: true
name: skills-authored-only-in-templates
summary: .claude/skills/ and .agents/skills/ are deployed artifacts, never edited
  directly. All skill changes go in packages/crypts-and-commits/src/cac/core/templates/skills/{claude,codex}/**,
  then the developer (never the agent) deploys them via `cac bootstrap init`. Check
  when an encounter's Plan touches skill behavior or wording.
updated_by: John Hoff
updated_on: '2026-07-28T03:53:02Z'
---

# Skills Are Authored Only in Templates

The working skill copies at `.claude/skills/` and `.agents/skills/` in this
repository are **deployed artifacts, not source**. They must never be edited
directly - not with `Edit`/`Write`, not via shell redirection or `sed -i`, no
matter how small the change.

All skill content changes are made in exactly one place:
`packages/crypts-and-commits/src/cac/core/templates/skills/{claude,codex}/{world_manager,campaign_manager}/SKILL.md`.
Once a template is edited, the developer - never the agent - deploys it into
the working copies by running `cac bootstrap init`
(`skills_core.deploy_skills` overwrites every deployed `SKILL.md`
unconditionally on each run). This is the same developer-only invocation
rule that already applies to bootstrap as a whole.

This supersedes any prior practice of hand-editing `.claude/skills/` or
`.agents/skills/` directly and separately back-porting the change into the
matching template. Templates are the only source of truth for skill content;
the working copies exist only to be overwritten.

When reviewing any encounter whose Plan touches skill behavior or wording:
confirm the Plan edits the template path, not the deployed `.claude/skills/`
or `.agents/skills/` path, and confirm it asks the developer to run
`cac bootstrap init` to deploy the change rather than attempting to deploy
it itself.
