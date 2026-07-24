---
campaign: v0.1.0-bootstrapping
created_by: John Hoff
created_on: '2026-07-24T04:54:40Z'
name: independent-review-subagent
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-07-24T05:31:30Z'
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

This is a **skill-only** change: no `cac` Python code is modified. Every edit
lands in the `campaign-manager` skill's `SKILL.md`. (MCP-driven enforcement of
the reading bound is future work, explicitly out of scope here.)

1. **Reviewer mechanism — fresh `general-purpose` subagent.** The
   `draft → reviewed` step spawns a fresh `general-purpose` agent via the Agent
   tool (`subagent_type: "general-purpose"`), explicitly **not** a fork, so it
   inherits none of the authoring conversation's context (guardrail 1). Only the
   agent's final report — findings + proposed review message + verdict — returns
   to the main thread. `general-purpose` is chosen over a read-only `Explore`
   agent because the review is a reasoning/critique task, not a code-locating
   fan-out; guardrail 4's reading bound is advisory (prompt-level) under either
   choice, so the read-only fence buys little here.

2. **Author the reviewer prompt template.** Add a verbatim, fill-in-the-blanks
   prompt block to `SKILL.md` that the main agent hands the subagent. It carries
   only the **encounter name** and **campaign name** — never pre-digested lore —
   and instructs the reviewer to:
   - **Prime context itself** (guardrail 1): run `cac world get`, enumerate
     world-assigned `enabled` lore via `cac lore list`/`get`, and for each region
     in the encounter's `regions` run `cac region get <region>` plus that
     region's `enabled` assigned lore. Read the encounter with
     `cac encounter get <name> -c <campaign>`.
   - **Check the Plan** against each applicable lore item.
   - **Stay within the bounded reading surface** (guardrail 4): read only the
     encounter body, applicable lore bodies (including any paths/globs the lore
     names), the assigned regions' documented `path`s, and files the Plan
     explicitly names. A lore-relevant area the Plan did not cite is **flagged as
     unverifiable / possibly out of scope**, not chased.
   - **Be critical, with a mandate to reject** (guardrail 2), returning exactly
     one verdict: **pass-with-notes**, **reject** (Plan conflicts with lore), or
     **not-reviewable / underspecified** (too vague to review within the cited
     surface).
   - **Produce findings plus a *proposed* `cac encounter review --message`
     string**, and run **no** `cac encounter` mutation itself (guardrail 3).
   The framing must stay neutral — the prompt must not argue the plan is sound.

3. **Rewrite the `draft → reviewed` section of `SKILL.md`.** Replace the current
   inline "gather lore / check the Plan / confirm / run review" text with:
   spawn the independent subagent → it primes lore and reviews within the bounded
   surface → it returns findings + proposed review message + verdict → the main
   thread relays them to the user → on user approval the main thread runs
   `cac encounter review <name> --message "<the reviewer's findings>"`. The
   message content is the reviewer's independent findings, replacing the acting
   agent's self-summary (per Requirements).

4. **State guardrail 4 as advisory** within the template: the reading bound is a
   prompt-level instruction, not a technical sandbox — nothing today denies an
   out-of-path read.

5. **Portability.** Keep the new wording free of hardcoded `.claude/skills/...`
   self-paths so it survives the planned move into
   `packages/crypts-and-commits/src/cac/core/templates/skills/`. Refer to the
   `cac` CLI and the `world-manager` skill by name, not by file path.

6. **Region note.** This encounter is assigned to the `crypts-and-commits`
   region, so its own review surface includes `console-best-practices`; since no
   `rich.Console`/CLI code changes here, that lore is satisfied vacuously.

## Verification

1. **Skill content review.** The `campaign-manager` `SKILL.md` `draft → reviewed`
   section instructs the independent-subagent flow with all four guardrails, the
   three verdicts, the bounded reading surface, and the human-held approval gate
   and transition. The reviewer prompt template is present and neutrally framed.
2. **Trial run.** Take a fresh draft encounter and invoke the new procedure,
   confirming the subagent (a) primes lore independently, (b) stays within the
   bounded reading surface, (c) can return a reject / underspecified verdict, and
   (d) leaves the `cac encounter review` transition to the human-approved main
   thread.
3. **Lint/tests (per `clean-tests-and-lint`).** Though the change is skill-only,
   run `pdm run pytest -q` and `pdm run ruff check .` / `pdm run ruff format .`;
   all must be clean (trivially, as no Python changes).

## Log

### Review - 2026-07-24T05:27:52Z - John Hoff

Inline lore review (draft->reviewed gate). Applicable lore: clean-tests-and-lint (world) and console-best-practices (crypts-and-commits region). clean-tests-and-lint: Plan is skill-only with no Python changes; Verification step 3 runs pytest -q and ruff check/format, honoring the gate. console-best-practices: no rich.Console/CLI code touched, so satisfied vacuously. No conflicts; Plan is reviewable and self-consistent as written. Locking sections.

### Opened - 2026-07-24T05:27:59Z - John Hoff

Opening to execute: skill-only edits to campaign-manager SKILL.md per the Plan.

### Message - 2026-07-24T05:30:40Z - John Hoff

Executed: campaign-manager SKILL.md rewritten. draft->reviewed now spawns a fresh general-purpose reviewer subagent (never a fork), with a neutral prompt template embodying all four guardrails (self-priming, bounded reading surface stated as advisory, flag-don't-chase, human-held approval+transition) and three verdicts (PASS-WITH-NOTES/REJECT/NOT-REVIEWABLE). Added 'Task' to allowed-tools. Verification: step 1 (content review) done; step 3 (clean-tests-and-lint) done - pytest 351 passed, ruff check clean, format no diffs. Step 2 (live trial run / dogfood) intentionally DEFERRED per user's decision to dogfood soon rather than now; encounter left open pending that trial before completion.

### Completed - 2026-07-24T05:31:30Z - John Hoff

Completing. Skill-only change delivered and verified (content review + clean-tests-and-lint: 351 tests pass, ruff clean). Live trial run (Verification step 2) deferred by GM decision to dogfood on the next fresh draft encounter rather than blocking this one; the new draft->reviewed procedure is documented and ready to exercise.
