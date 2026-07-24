---
campaign: v0.1.0-bootstrapping
created_by: John Hoff
created_on: '2026-07-24T04:54:40Z'
name: independent-review-subagent
regions: []
status: draft
updated_by: John Hoff
updated_on: '2026-07-24T04:54:40Z'
---

# Independent Review Subagent for the Encounter Lore Review

## Requirements

The `draft → reviewed` lore-review gate must be performed by an **independent,
fresh subagent**, not inline by the acting agent that authored the plan. The
subagent primes the world/lore itself in a clean session and checks the plan
against applicable lore, subject to four guardrails:

1. **Fresh agent, never a fork.** It must not inherit the authoring
   conversation's context (a fork would reproduce the author's bias). It runs
   `world-manager` itself to prime the world summary and applicable lore in a
   clean session.
2. **Neutral, minimal prompt with a mandate to reject.** The prompt must not
   argue for the plan ("here's why it's sound"). It instructs the reviewer to
   be critical and permits a verdict of "not reviewable as written."
3. **The human GM keeps the approval gate and the transition.** The subagent
   produces findings plus a *proposed* review message; it does **not** run
   `cac encounter review`. The main thread relays the findings, the user
   approves, and the transition fires from the main thread.
4. **Bounded reading surface.** The reviewer may *read* only: the encounter
   body, the applicable lore bodies (including any paths/globs the lore names),
   the assigned regions' documented paths, and files the Plan explicitly names.
   A suspected lore-relevant area the plan did **not** cite must be **flagged as
   unverifiable / possibly out-of-scope**, not chased — bound reading, not
   suspicion.

The reviewer's independent findings become the content of the
`cac encounter review --message`, replacing the acting agent's self-summary.

## Rationale

The acting agent reviewing its own plan against lore is a conflict of interest:
it shares the author's priors and rationalizations, so the review collapses into
a consistency check against those priors — a rubber stamp. A cold subagent is
structurally independent of the authoring conversation and reads the encounter
*as written*, which also tests whether the encounter is self-contained enough to
survive a context reset — CAC's core premise.

Guardrail 4 bounds token consumption and reinforces the correct behavior
(review the *plan*, don't do repo archaeology), while "flag, don't chase"
preserves the reviewer's most valuable output — catching sins of omission —
without unbounded digging. When a plan is too vague to review within its cited
surface, the correct verdict is "underspecified," not "reverse-engineer intent
from the whole repo."

Caveat to carry into the design: guardrail 4 is a **prompt-level** boundary, not
a technical sandbox — there is no mechanism today that denies reads outside a
path. It should be stated as advisory; a read-only/Explore-style toolset plus
the region path as a fence can tighten it, but not enforce it.

## Plan

*(To be developed in a fresh context — this draft captures the decision, not the
final implementation.)*

- Choose the mechanism: which subagent type (a fresh `general-purpose` or
  read-only `Explore`-style agent, explicitly **not** a fork), how it is
  invoked from the `campaign-manager` review step, and how findings return to
  the main thread.
- Author the reviewer prompt template embodying guardrails 1-4, including the
  allowed-reading-surface definition and the "flag, don't chase" instruction,
  and the permitted verdicts (pass-with-notes / reject / not-reviewable).
- Update `.claude/skills/campaign-manager/SKILL.md`, `draft → reviewed`:
  replace the inline "gather lore / check the Plan" step with "spawn an
  independent review subagent → it primes lore and reviews within the bounded
  surface → it returns findings + a proposed review message → the user confirms
  → the main thread runs `cac encounter review`."
- Decide whether any of this belongs in code (e.g. a future MCP-driven flow)
  versus skill instructions only. Skill-only is the expected answer for now.
- Keep the wording portable against the planned move of skills into
  `packages/crypts-and-commits/src/cac/core/templates/skills/` (per CLAUDE.md).
- Decide whether this encounter should be assigned to the `crypts-and-commits`
  region (the skills' eventual home) or left region-less while the skills still
  live under `.claude/skills/`.

## Verification

- The `campaign-manager` skill clearly instructs the independent-subagent review
  with all four guardrails and the human-held approval gate.
- Trial run: take a fresh draft encounter, invoke the new review procedure, and
  confirm the reviewer (a) primes lore independently, (b) stays within the
  bounded reading surface, (c) can return a reject / underspecified verdict, and
  (d) leaves the `cac encounter review` transition to the human-approved main
  thread.
- If any code changes are introduced, `pdm run pytest -q` passes and
  `pdm run ruff check .` / `ruff format .` are clean (per `clean-tests-and-lint`).
