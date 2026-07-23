---
assigned_lore:
- clean-tests-and-lint
name: Crypts and Commits
---

# Crypts and Commits

Crypts and Commits ("CAC") is a Coding Assistant Continuity Framework: a way of structuring collaboration between a developer and an AI coding assistant using a tabletop-gaming metaphor. The developer plays Game Master, establishing context, making judgment calls, and retaining final authority over the session; the assistant plays through that context to get work done. The `cac` CLI is the tool an assistant uses to record project context and track its own work across sessions, so continuity survives context resets and session boundaries instead of being rebuilt from scratch each time.

This repository is both the framework's implementation and its first user: as `cac` is built out, this project's own `.sourcebook` is being bootstrapped and driven through the same CLI, ahead of the longer-term goal of using CAC to drive AI-assisted work on other projects.

## Domain model

- **World** (this file) - project-level summary, read first to prime context.
- **Lore** - standards, conventions, and best practices used to review an encounter's plan before work starts. World-assigned lore is global; region-assigned lore only applies within that region.
- **Region** - a documented path within the repository (e.g. frontend vs. backend) that carries its own conventions and lore.
- **Campaign** - a long-running initiative, analogous to a Jira Epic, expected to span many encounters.
- **Encounter** - a concrete unit of work within a campaign: a plan with Requirements, Rationale, Plan, and Verification sections, carried through a draft -> open -> completed lifecycle (or abandoned at any point).

## Guardrail

`.sourcebook/` content is managed exclusively through the `cac` CLI, never by editing files under it directly. `cac bootstrap init` is run by the developer only - never by the assistant.
