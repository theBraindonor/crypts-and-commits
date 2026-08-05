---
archived: false
campaign: v0.1.8-release-readiness
created_by: John Hoff
created_on: '2026-08-05T02:41:54Z'
depends_on: []
name: add-unscripted-encounter-subtype
regions:
- crypts-and-commits
status: draft
updated_by: John Hoff
updated_on: '2026-08-05T02:41:57Z'
---

# Encounter

## Requirements

- Introduce an "unscripted encounter" subtype that captures manual changes made by the developer or the coding assistant outside the context of a pre-planned encounter, so the intent behind those changes is preserved for subsequent agent use.
- Represent the subtype as a new encounter frontmatter field (e.g. `kind`), defaulting to the existing behavior ("scripted") for every current and future normally-planned encounter, with "unscripted" as the alternate value.
- An unscripted encounter follows the same `draft` -> `reviewed` -> `open` -> `completed` (or `abandoned`) status lifecycle as a scripted encounter, including the independent-reviewer gate at `draft` -> `reviewed` and the developer approval gates around it - but only `Requirements` and `Rationale` are required/applicable. `Plan` and `Verification` are not applicable to this kind and must not be enforced the way they are (implicitly, by convention) for scripted encounters.
- Region assignment remains required before review, unchanged from scripted encounters.
- The subtype must be surfaced consistently across `core/encounter.py`, `cli/encounter.py`, `mcp/encounter.py`, and `docs/workflow.md`, per the `cli-mcp-parity` and `workflow-doc-source-of-truth` region lore.

## Rationale

Today, `.sourcebook` only models work that goes through the full plan-first encounter flow. In practice, both the developer and the coding assistant sometimes make manual changes outside that flow - direct edits, quick fixes, exploratory changes - and that work's *intent* currently has nowhere to be recorded, so a later session has no way to recover why it happened.

An unscripted encounter gives that manual work a place to be captured after the fact: Requirements and Rationale describe what was done and why, without forcing a Plan/Verification that don't apply to work that's already happened. Running the encounter through the same full review lifecycle (rather than skipping straight to a closed/recorded state) is deliberate: it gives the independent reviewer a chance to check the recorded intent against project lore, and gives the coding assistant an opportunity to make follow-up changes based on that review - the same value the review gate provides for scripted encounters, just applied to a record of completed work instead of a plan for future work.

## Plan

Plan has not been described yet.

## Verification

Verification has not been described yet.
