---
campaign: v0.1.5-generate-and-integrate-documentation
created_by: John Hoff
created_on: '2026-08-02T16:45:53Z'
depends_on: []
name: add-quickstart-guide
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-08-02T16:51:26Z'
---

## Requirements

- A new `docs/QUICKSTART.md` at the repository root walks a developer adopting `crypts-and-commits` in their own project through exactly three steps: (1) install the package, (2) run `cac bootstrap init` in their project root, (3) hand off to their coding assistant to flesh out `.sourcebook/world.md` (and, as needed, lore/regions) via the `world-manager` skill that bootstrap just deployed.
- Step 1's install instructions use `pip install "git+https://github.com/theBraindonor/crypts-and-commits.git#subdirectory=packages/crypts-and-commits"` (the package is not yet published to PyPI - no `.github` publish workflow exists - so a PyPI-style `pip install crypts-and-commits` would be inaccurate).
- The guide stays install/setup-focused and does not restate the `.sourcebook` domain model or workflow procedure - that's `docs/workflow.md`'s job (`packages/crypts-and-commits/src/cac/core/templates/docs/workflow.md`), reachable by an agent on demand via `docs_get("workflow")`/`cac docs get workflow` once bootstrapped. The guide's job is getting a human from zero to "an agent session can now take over," not re-explaining what CAC is or how its lifecycle works.
- The guide notes that `cac bootstrap init` deploys the MCP server registration, the `.sourcebook/` guardrail, and both `world-manager`/`campaign-manager` skill flavors in the same step - so step 3 (asking the agent to flesh out the world file) works immediately afterward with no further manual setup.
- Root `README.md` links to `docs/QUICKSTART.md` (a short "Quickstart" pointer near the top of the file).
- `packages/crypts-and-commits/README.md` links to the same guide, for consistency with the root README and for anyone landing on that package's README directly (e.g. a future PyPI project page).

## Rationale

A developer evaluating or adopting CAC for the first time has no agent session running yet - that's a cold-start gap the new `docs` MCP/CLI tool from the previous encounter doesn't cover, since it's agent-only. A short, install-focused quickstart linked from both READMEs closes that gap without duplicating `workflow.md`'s depth: the boundary is deliberate, mirroring the same "don't carry deep detail in project docs, pull it in only when needed" principle the docs tool encounter established, just for the human side instead of the agent side. The existing root `docs/` directory (already holding `context-management-design.md` and `encounter-search-design.md`) is the natural home, rather than inventing a new location.

## Plan

1. Write `docs/QUICKSTART.md`: three numbered steps (install via the git-based `pip install` command, run `cac bootstrap init`, then ask the coding assistant to flesh out the world file), kept short - no restatement of the domain model or workflow procedure, just a pointer to the fact that the agent has what it needs (skills + docs tool) once bootstrap completes.
2. Update root `README.md`: add a short "Quickstart" pointer near the top linking to `docs/QUICKSTART.md`.
3. Update `packages/crypts-and-commits/README.md`: add the same quickstart link.
4. Confirm no lore in the `crypts-and-commits` region's assigned set (`cli-mcp-parity`, `console-best-practices`, `skills-authored-only-in-templates`, `workflow-doc-source-of-truth`) applies - this Plan touches no CLI/MCP code, no `core/` status lifecycle, no skill template, and no console output, so none of the four are triggered; note this explicitly for the reviewer rather than leaving it to be assumed.
5. Run `pdm run pytest -q` and `pdm run ruff check .` / `pdm run ruff format .` to confirm the (docs-only) change didn't break anything.

## Verification

- `pdm run pytest -q` passes in full.
- `pdm run ruff check .` reports zero errors; `pdm run ruff format .` reports no diffs.
- Manually re-read `docs/QUICKSTART.md` against the current `cac bootstrap init --help` output and this repo's actual bootstrap behavior (MCP registration, guardrail, skill deployment) to confirm every claim is accurate, not aspirational.
- Confirm both README links resolve to the correct relative path before asking the user to confirm completion.

## Log

### Review - 2026-08-02T16:47:51Z - John Hoff

Reviewed against all five applicable lore items (world: clean-tests-and-lint; region crypts-and-commits: cli-mcp-parity, console-best-practices, skills-authored-only-in-templates, workflow-doc-source-of-truth). The Plan's own step-4 audit correctly concludes the four region-scoped lore items are inapplicable since this is a docs/README-only change touching no cli/, mcp/, core/, or skill-template code, and the clean-tests-and-lint gate is properly included via Plan step 5 and the Verification section. One non-blocking note: the encounter's actual targets (docs/QUICKSTART.md, root README.md) sit outside the assigned region's documented path (packages/crypts-and-commits), which I flag but did not chase since it falls outside the reviewer's bounded reading surface — worth a quick sanity check that no other region/lore should have been in scope. No conflicts found; approved to proceed.

### Completed - 2026-08-02T16:51:26Z - John Hoff

docs/QUICKSTART.md added with the three-step install/bootstrap/hand-off flow, verified against cac bootstrap init's actual implementation (bootstrap.py + cli/bootstrap.py). Root README.md links via a relative path; packages/crypts-and-commits/README.md links via an absolute GitHub URL so the link survives a future standalone PyPI publish. Full pytest suite (708 tests) and ruff clean.
