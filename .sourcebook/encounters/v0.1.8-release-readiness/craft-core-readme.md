---
archived: false
campaign: v0.1.8-release-readiness
created_by: John Hoff
created_on: '2026-08-05T02:44:46Z'
depends_on: []
name: craft-core-readme
regions:
- crypts-and-commits
status: draft
updated_by: John Hoff
updated_on: '2026-08-05T02:45:18Z'
---

# Encounter

## Requirements

- Produce a polished, public-facing README that serves as the project's first impression for external users and, once the package is published, the content rendered on its PyPI package page (`packages/crypts-and-commits/README.md` is the package's own `pyproject.toml` `readme`, distinct from the root `README.md`, which describes the PDM workspace as a whole - confirm during drafting whether one or both need this treatment).
- Cover, at minimum: what CAC is and the problem it solves, install/quickstart, a pointer to the full [Quickstart guide](docs/QUICKSTART.md), license, and pointers to further documentation.
- Content must be accurate against the project's actual current capabilities and installation method (currently a git-URL install per `docs/QUICKSTART.md`, pending whatever this campaign's packaging/versioning work lands) - no aspirational functionality (e.g. `demo-ui` doesn't exist yet).

## Rationale

The package's current README (`packages/crypts-and-commits/README.md`) is a two-sentence stub with no install instructions, usage example, or license reference - not something that would land a first-time visitor or a PyPI browser. The release-readiness campaign body explicitly calls out README accuracy as a gating concern for the public package page, and this is currently the largest gap against that bar.

This encounter records the punchlist item itself; the actual content and final root-vs-package scope are deferred to when the encounter is picked up for work, not decided here.

## Plan

Plan has not been described yet.

## Verification

Verification has not been described yet.
