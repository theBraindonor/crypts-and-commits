---
archived: false
campaign: v0.1.8-release-readiness
created_by: John Hoff
created_on: '2026-08-05T02:44:46Z'
depends_on: []
name: craft-core-readme
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-08-09T06:15:15Z'
---

# Encounter

## Requirements

- Produce a polished, public-facing README for `packages/crypts-and-commits/README.md` — the package's own `pyproject.toml` `readme`, and therefore the content PyPI renders on the package's page once published. Scope confirmed on pickup: **package README only**. The root `README.md` is out of scope here — its own README/QUICKSTART/per-package navigation pass is tracked separately by the `documentation-continuity-pass` encounter in this campaign.
- Cover, at minimum: what CAC is and the problem it solves, install instructions, a pointer to the full [Quickstart guide](docs/QUICKSTART.md), a license reference, and pointers to further documentation.
- Install instructions: write the standard `pip install crypts-and-commits` form, confirmed on pickup — not today's git-URL install (`docs/QUICKSTART.md`'s current method). Rationale: this README's install line will only actually be read by anyone once the package is live on PyPI, at which point plain `pip install` is what will be true, so writing it now is not aspirational relative to its actual audience, unlike a claim about existing functionality. `docs/QUICKSTART.md` (out of scope here) keeps documenting today's git-URL method separately until packaging/publishing work lands.
- All links into repository content that lives outside `packages/crypts-and-commits/` (e.g. `docs/QUICKSTART.md`, the root `LICENSE`) must use absolute GitHub URLs (`https://github.com/theBraindonor/crypts-and-commits/blob/main/...`), not repo-relative paths — this README ships standalone inside the built sdist/wheel and renders on PyPI without surrounding repo context, so a relative link to a path the package doesn't contain would 404. The existing stub already does this correctly for its one link; every new link added must follow the same rule.
- Content must be accurate against the project's actual current capabilities — no aspirational functionality (e.g. don't reference `demo-ui`, CI badges, or a specific version number, none of which exist/are stable yet).

## Rationale

The package's current README (`packages/crypts-and-commits/README.md`) is a two-sentence stub with no install instructions, usage example, or license reference — not something that would land a first-time visitor or a PyPI browser. The release-readiness campaign body explicitly calls out README accuracy as a gating concern for the public package page, and this is currently the largest gap against that bar.

## Plan

1. Rewrite `packages/crypts-and-commits/README.md` with these sections, in order:
   - **Title + intro** — keep the existing framing (CAC name, tabletop-gaming/Game-Master metaphor, developer retains final authority), expanded slightly into 2-3 sentences covering what problem it solves (continuity of AI-coding-assistant context/work-tracking across sessions).
   - **Install** — a fenced `pip install crypts-and-commits` block, per the confirmed decision above.
   - **Quickstart** — one or two sentences on what `cac bootstrap init` does (bootstraps `.sourcebook/`, registers the MCP server, deploys agent skills), then a pointer to the full [Quickstart guide](https://github.com/theBraindonor/crypts-and-commits/blob/main/docs/QUICKSTART.md) (absolute URL, per the link rule above) for the complete walkthrough.
   - **What's inside** — a short domain-model summary (world / lore / region / campaign / encounter) and a one-line mention that both a `cac` CLI and a `cac-mcp` MCP server console script ship, since an agent typically drives the MCP tools directly.
   - **Documentation** — pointer to the project repository (`https://github.com/theBraindonor/crypts-and-commits`) for the full development workspace (including the demo apps), and a one-line mention that deeper framework reference docs (e.g. the workflow guide) are available on demand via the `docs` CLI/MCP tools once bootstrapped.
   - **License** — state Apache-2.0, linking to the absolute GitHub URL for `LICENSE`.
2. Read back the rewritten file once and check it against every bullet in Requirements above (scope, install method, absolute-vs-relative links, no aspirational content, "CAC" not "C&C" per project convention).
3. Run the project's standard verification gate (below).

## Verification

- `pdm run pytest -q` passes (run from the repository root) — expected to be unaffected by a docs-only change, but this is the project's standard completion gate and must still be run and pass.
- `pdm run ruff check .` reports zero errors and `pdm run ruff format .` reports no diffs (per the `clean-tests-and-lint` gate lore) — expected no-ops for a `.md`-only change, but run both to confirm.
- Manual read-through of the rendered `packages/crypts-and-commits/README.md` confirming: both links (`QUICKSTART.md`, `LICENSE`) are absolute GitHub URLs and resolve correctly; the install line reads `pip install crypts-and-commits`; no mention of `demo-ui`, CI badges, or a specific version number; "CAC" used throughout, never "C&C".
- User confirms the rendered content reads well before the encounter is marked complete.

## Log

### Review - 2026-08-09T06:10:38Z - John Hoff

Reviewed against all five applicable lore items (clean-tests-and-lint, cli-mcp-parity, console-best-practices, skills-authored-only-in-templates, workflow-doc-source-of-truth): clean-tests-and-lint is directly and correctly addressed in Verification (pytest + ruff gate); the other four are region-assigned but not substantively triggered by this docs-only README rewrite, and the Plan introduces no conflicts with any of them. Spot-checked the Plan's factual claims against packages/crypts-and-commits/pyproject.toml (the cac/cac-mcp console scripts and Apache-2.0 license both confirmed accurate) and the existing README stub (its link is already an absolute GitHub URL, consistent with the Plan's link rule). The Plan is concrete, scoped correctly (package README only, root README explicitly deferred to a separate encounter), avoids all named aspirational content, and includes explicit self-verification steps for the link-format and CAC-naming conventions. No lore conflicts found.

### Completed - 2026-08-09T06:15:15Z - John Hoff

Rewrote packages/crypts-and-commits/README.md per the Plan: Install/Quickstart/What's inside/Documentation/License sections, standard pip install line, absolute GitHub URLs for links outside the package, no aspirational content. Verification gate passed (pdm run pytest -q: 804 passed; ruff check and format clean). User reviewed the rendered content and requested one follow-up edit (crediting the cac-mcp MCP server alongside the CLI in the intro paragraph, not just the CLI), which was applied and re-verified before completion.
