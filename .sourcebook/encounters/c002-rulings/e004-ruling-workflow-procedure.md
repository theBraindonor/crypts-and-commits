---
archived: false
campaign: c002-rulings
created_by: John Hoff
created_on: '2026-11-21T02:51:11Z'
depends_on:
- e003-ruling-prime-exposure
kind: scripted
name: e004-ruling-workflow-procedure
regions:
- crypts-and-commits
status: draft
updated_by: John Hoff
updated_on: '2026-11-21T02:51:12Z'
---

## Requirements

Add the agent procedure for rulings to the packaged Workflow Reference Guide (`templates/docs/workflow.md`), per `b005-ruling-records`: capture during an open campaign, including the reason for a reviewer REJECT override, and planning triage (canonize with lore changes, or note, then archive). e001–e003 already documented the domain model, lifecycle, search and prime exposure. What is missing is the procedure in "Explicit user gates → Review flow" and "Agent planning and campaign workflow".

Edits to `workflow.md`:

1. **Ownership.**
   - world-planner also triages integrated recorded rulings (canonize or note) and archives them.
   - campaign-manager's execution includes ruling capture.
2. **Allocate numbers.** Add a Rulings bullet: rulings are not numbered. Each is named `cNNN-eNNN-slug` for the open campaign and the current encounter (`e000` when none), with a slug unused among live and archived rulings.
3. **New subsection "Capture rulings"**, after "Execute on the campaign branch":
   - **When:** the developer confirms an answer to an open question or choice during an open campaign. Examples are a boss or encounter open question, a plan choice, or the reason for overriding a reviewer REJECT. The ruling is recorded in the same exchange.
   - **Who:** any skill working in the open campaign does this, not only campaign-manager.
   - **What:** only what the developer confirmed (the decision, its context and consequences), with the developer as origin.
   - **Do not filter:** never ask whether a decision is important enough, because planning decides that in hindsight.
   - **What it does not replace:** a ruling never replaces the encounter's own record. Plan deviations still go to the encounter log, and follow-up ideas for a frozen boss still become rumors.
   - **Approval:** capture needs no separate approval gate, but a ruling's meaning is never rewritten without the developer.
   - **No open campaign:** capture a rumor instead.
4. **Review flow.** The developer may override a REJECT with a stated reason. The agent then records the review with `encounter_review`, using a message that states the GM override and its reason, and captures that reason as a ruling. Otherwise the encounter stays in draft and is revised, as today.
5. **Planning handoff.** world-planner also triages integrated recorded rulings, which prime lists:
   - Hydrate each ruling and decide with the developer.
   - **Canonize:** after making the lore, region or world changes the developer approves, through the normal tools, canonize with a narrative of what changed.
   - **Note:** note with a narrative of why no change is needed.
   - **Superseded rulings:** a ruling superseded by a later ruling is noted, with a narrative naming its successor.
   - **Archive:** archive each ruling once it has a disposition. Rulings are never deleted.
   - **Branches:** rulings reach planning only by integrating their execution branch, and their names never collide, because campaign numbers are settled at assignment.

`tool-reference.md`: no change. This encounter changes no tool name, argument, result, error or budget, and e001–e003 already documented the ruling tools, search type and prime fields.

## Rationale

`workflow-doc-source-of-truth` makes `workflow.md` the owner of skill procedure: gates, review flow, and planning and campaign procedure. b005's success criteria call for skill guidance on capture and triage, and the guide must describe that procedure. The procedure text is authored here first. The next c002 encounter brings both provider variants of the world-planner and campaign-manager skill templates in line with it. This encounter touches no skill template, so no template drifts from the guide in the meantime. The templates are not redeployed into this repository until the developer runs `cac bootstrap init` after the campaign.

**Capture is guidance, not enforcement** (b005 scope: "not a rule enforced by core"). It leans on the way agents already ask and resolve open questions with the developer, which keeps the developer's confirmation as the trigger instead of adding a new gate.

**The REJECT override** formalizes existing practice (offer an explicit GM override, logged as such), and b005 names its reason as a ruling trigger.

**Size.** The additions are written to fit the stopgap cap of 45,000 characters (ruling `c002-e001-workflow-cap-stopgap`). The guide is about 40,840 characters, and the additions are budgeted at roughly 2,500.

**Out of scope:**
- Skill template text (next c002 encounter).
- The branching guide, migration guide, `CLAUDE.md`/`AGENTS.md` and public docs (final c002 encounter).
- Splitting the guide (rumor r004).

## Plan

1. Edit `packages/crypts-and-commits/src/cac/core/templates/docs/workflow.md` with the five changes listed in Requirements, in the existing concise prose style, keeping current wording elsewhere intact.
2. Check the result against b005's Scope and model and Success Criteria. Every procedure claim must match shipped behavior:
   - capture only in an `open` campaign, including a reactivated one;
   - `e000` for no encounter;
   - narratives required for canonize and note;
   - archive only after a disposition;
   - no delete and no formal lore links.
3. Make no code changes. Run the full suite, including the `test_docs` size cap and repository-name leak guard.

## Verification

- `pdm run pytest -q` passes, including `tests/core/test_docs.py`: the guide is at most 45,000 characters, and no repository campaign or encounter names leak, `e000` excepted. No skips or deletions are added to dodge failures.
- `pdm run ruff format .` has been applied, and then `pdm run ruff check .` and `pdm run ruff format --check .` are clean.
- `docs_get("workflow")` (or `cac docs get workflow`) returns the updated guide and fits the docs response budget.
- Reading the diff against b005 and the shipped tools confirms:
  - each of the five edits is present;
  - no statement contradicts e001–e003 behavior (capture guard, lifecycle, archival independence, prime and search);
  - `tool-reference.md` needs no change.
