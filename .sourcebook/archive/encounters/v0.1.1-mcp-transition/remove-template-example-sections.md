---
archived: true
campaign: v0.1.1-mcp-transition
created_by: John Hoff
created_on: '2026-07-25T19:47:13Z'
depends_on: []
name: remove-template-example-sections
regions: []
status: completed
updated_by: John Hoff
updated_on: '2026-08-02T22:11:30Z'
---

## Requirements

- Remove the `## Example` subheading and its sample content from the three sourcebook
  templates that have it: `packages/crypts-and-commits/src/cac/core/templates/sourcebook/campaign.md`,
  `lore.md`, and `region.md`.
- Leave the rest of each template unchanged: frontmatter, `# <Title>` heading, and the
  single "This <thing> has not been described yet." placeholder line under it.
- `encounter.md` and `world.md` do not have an `Example` section and are out of scope.
- No test currently asserts on the `Example` section's content (confirmed by grep), so no
  test changes are required; the placeholder-text assertions in `test_campaign.py`,
  `test_lore.py`, and `test_region.py` continue to pass unchanged.

## Rationale

`campaign.md`, `lore.md`, and `region.md` each carry a `## Example` subheading with sample
prose illustrating what a good body looks like. `cac campaign/lore/region create` without
`--body` opens `$EDITOR` pre-filled with the full template body (via `template_body()` /
`edit_markdown`), so a developer who doesn't manually delete the Example section before
saving ends up with it baked into the real, persisted body — the illustrative text "leaks"
into created content instead of staying documentation-only. Removing the section removes
the leak at its source.

## Plan

1. Edit `templates/sourcebook/campaign.md` to delete the `## Example` heading and its
   paragraph/blockquote, leaving just the placeholder line under `# Campaign`.
2. Apply the same removal to `templates/sourcebook/lore.md` and `templates/sourcebook/region.md`.
3. Run `pdm run ruff format .` and `pdm run ruff check .` to confirm formatting/lint stay clean
   (these are markdown template files, not Python, but run the gate per world lore regardless).
4. Run `pdm run pytest -q` to confirm the full suite still passes unchanged.

## Verification

- `pdm run pytest -q` passes with no skips or deletions.
- `pdm run ruff check .` reports zero errors; `pdm run ruff format .` reports no diffs.
- Manual read of the three edited template files confirms no `## Example` heading remains
  and the placeholder line is intact.

## Log

### Review - 2026-07-25T19:48:21Z - John Hoff

The Plan directly satisfies the sole applicable lore item, clean-tests-and-lint (world-assigned; no regions are attached to this encounter, so no region-scoped lore applies): it runs pdm run ruff format . / pdm run ruff check . and pdm run pytest -q as explicit steps, and the Verification section mirrors that same gate without skips, deletions, or suppressions. Direct inspection of the three named template files (campaign.md, lore.md, region.md) confirms the Plan's description of their current structure is accurate and the proposed edit (removing only the ## Example heading and its sample content, leaving frontmatter and the placeholder line intact) is precisely scoped. One unverified claim outside the bounded reading surface: the Requirements section asserts, via an uncited grep, that no test asserts on the Example section's content and that test_campaign.py/test_lore.py/test_region.py need no changes - this was not independently confirmed and should be spot-checked during execution rather than taken purely on faith.

### Completed - 2026-07-25T19:49:59Z - John Hoff

Removed the ## Example subheading and sample content from campaign.md, lore.md, and region.md, leaving frontmatter and the single placeholder line intact. Verified: pdm run ruff format . (96 files unchanged) and ruff check . (all checks passed) both clean; pdm run pytest -q passed 504/504. Manual read confirmed no Example heading remains in any of the three files.
