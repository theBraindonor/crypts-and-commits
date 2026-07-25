---
campaign: v0.1.0-bootstrapping
created_by: John Hoff
created_on: '2026-07-25T01:22:33Z'
name: 07-depends-on-frontmatter-field
regions:
- crypts-and-commits
status: draft
updated_by: John Hoff
updated_on: '2026-07-25T01:23:07Z'
---

# Depends-On Frontmatter Field

## Requirements

- Add a `depends_on` field to encounter frontmatter: a list of encounter names (within the same campaign) that an encounter depends on.
- This provides a graph-based execution ordering of encounters, so that when an initiative is broken into multiple encounters the correct order is captured on the objects themselves rather than only implied by a manual name-prefix convention.
- Provide a way to inspect/derive dependency order (e.g., `encounter list` reflecting or validating a topological order — to be detailed).
- Validation to consider: referenced encounters must exist within the campaign; dependency cycles must be rejected (to be detailed).
- CLI affordance to assign and unassign dependencies (to be detailed).

## Rationale

_To be detailed when this encounter is picked up._ (Seed motivation: this initiative used a manual numeric name-prefix to convey creation/execution order; a first-class `depends_on` field replaces that convention with an inspectable dependency graph for future multi-encounter initiatives.)

## Plan

_To be detailed when this encounter is picked up._

## Verification

_To be detailed when this encounter is picked up._
