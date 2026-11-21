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
updated_on: '2026-11-21T02:55:47Z'
---

## Requirements

Add the agent procedure for rulings to the packaged Workflow Reference Guide (`templates/docs/workflow.md`), per `b005-ruling-records`: capture during an open campaign, including the reason for a reviewer REJECT override, and planning triage (canonize with lore changes, or note, then archive). e001–e003 already documented the domain model, lifecycle, search and prime exposure. What is missing is the procedure. The guide must stay internally consistent: every existing passage that the new procedure would make inaccurate is updated in the same change.

Edits to `workflow.md`:

1. **Ownership.**
   - world-planner also triages integrated recorded rulings (canonize or note) and archives them.
   - Ruling capture is not owned by one skill. It is phrased the way the guide already treats rumors ("any skill captures…"): any skill working in an open campaign captures rulings, including campaign-manager during execution. The Ownership list and the new subsection must not read as conflicting.
2. **Allocate numbers.** Add a Rulings bullet: rulings are not numbered. Each is named `cNNN-eNNN-slug` for the open campaign and the current encounter (`e000` when none), with a slug unused among live and archived rulings.
3. **New subsection "Capture rulings"**, after "Execute on the campaign branch":
   - **When:** the developer confirms an answer to an open question or choice during an open campaign, such as a boss or encounter open question, a plan choice, or the reason for overriding a reviewer REJECT. The ruling is recorded in the same exchange.
   - **Who:** any skill working in the open campaign.
   - **What:** only what the developer confirmed (the decision, its context and consequences), with the developer as origin.
   - **Do not filter:** never ask whether a decision is important enough, because planning decides that in hindsight.
   - **What it does not replace:** a ruling never replaces the encounter's own record. Plan deviations still go to the encounter log, and follow-up ideas for a frozen boss still become rumors.
   - **Approval:** capture needs no separate approval gate, but a ruling's meaning is never rewritten without the developer.
   - **No open campaign:** capture a rumor instead.
4. **REJECT override, defined once and reflected everywhere it applies.**
   - **Review flow** gets the definition:
     - The agent may offer the developer an explicit GM override of a REJECT. It is never assumed or self-granted.
     - If the developer overrides with a stated reason, that decision is the developer's explicit draft-to-reviewed authorization. The agent records `encounter_review` with a message that keeps the reviewer's findings verbatim or faithfully transcribed, then states the GM override and its reason.
     - The agent captures the reason as a ruling.
     - NOT-REVIEWABLE has no override path: the draft is revised.
     - Without an override, the encounter stays in draft and is revised, as today.
   - **Explicit user gates:**
     - Gate 1 is unchanged.
     - The text explaining how an encounter reaches reviewed adds that a GM override of a REJECT is the other path. Like PASS-WITH-NOTES, it needs no further pause, because the developer's override is the approval.
     - Gate 2 (separate approval to open) still applies after an override, and the "Not separately gated" paragraph is updated to match.
   - **Codex encounter handoffs:** the "After every review" paragraph currently says "On REJECT or NOT-REVIEWABLE, keep the draft…". It gains the override path: after a developer override, transition first with the override message, report, and ask separately to open. Otherwise keep the draft as today.
   - **Example: an encounter's lifecycle**, step 5: "On REJECT or NOT-REVIEWABLE, revise and ask again" gains "or, on REJECT, the developer may override with a reason, which is recorded and captured as a ruling".
5. **Planning handoff.** world-planner also triages integrated recorded rulings, which prime lists:
   - Hydrate each ruling and decide with the developer.
   - **Canonize:** after making the lore, region or world changes the developer approves, through the normal tools, canonize with a narrative of what changed.
   - **Note:** note with a narrative of why no change is needed.
   - **Superseded rulings:** a ruling superseded by a later ruling is noted, with a narrative naming its successor.
   - **Archive:** archive each ruling once it has a disposition. Rulings are never deleted.
   - **Branches:** rulings reach planning only by integrating their execution branch, and their names never collide, because campaign numbers are settled at assignment.

`tool-reference.md`: no change. This encounter changes no tool name, argument, result, error or budget, and e001–e003 already documented the ruling tools, search type and prime fields. `encounter_review` already requires only a nonblank message and an assigned region, not a verdict, so the override needs no contract change.

## Rationale

`workflow-doc-source-of-truth` makes `workflow.md` the owner of skill procedure: gates, review flow, and planning and campaign procedure. A substantive change must keep every statement in the guide accurate. An earlier draft of this encounter added the REJECT override only to Review flow, which would have left three passages contradicting it. This revision updates every passage the override touches and adds an internal-consistency check to Verification.

b005's success criteria call for skill guidance on capture and triage. The procedure text is authored here first, and the next c002 encounter brings both provider variants of the world-planner and campaign-manager skill templates in line with it. That includes carrying the override path into both campaign-manager templates' gate wording, which "Explicit user gates" requires them to state in their own words. This encounter touches no skill template, and templates are not redeployed into this repository until the developer runs `cac bootstrap init` after the campaign, so nothing drifts in practice.

**Capture is guidance, not enforcement** (b005 scope: "not a rule enforced by core"). It leans on the way agents already ask and resolve open questions with the developer, so the developer's confirmation is the trigger and no new gate is added.

**The REJECT override** formalizes existing practice: the agent offers an explicit GM override, which is logged as such. b005 names the override reason as a ruling trigger. Keeping the reviewer's findings intact in the review message preserves the rule that the agent never replaces or rewrites the reviewer's recorded findings. NOT-REVIEWABLE has no override because there is nothing reviewable to accept.

**Size.** The additions are written to fit the stopgap cap of 45,000 characters (ruling `c002-e001-workflow-cap-stopgap`). The guide is about 40,840 characters, and the additions are budgeted at roughly 3,000.

**Out of scope:**
- Skill template text (next c002 encounter).
- The branching guide, migration guide, `CLAUDE.md`/`AGENTS.md` and public docs (final c002 encounter).
- Splitting the guide (rumor r004).

## Plan

1. Edit `packages/crypts-and-commits/src/cac/core/templates/docs/workflow.md` with the five changes listed in Requirements, including all four override touchpoints: Review flow, Explicit user gates, Codex encounter handoffs, and the lifecycle example. Use the existing concise prose style, and keep unrelated wording intact.
2. Search the whole guide for every statement about REJECT, NOT-REVIEWABLE, reaching reviewed, the gates, rumor capture ownership and rulings, and confirm each one agrees with the new text.
3. Check the result against b005's Scope and model and Success Criteria. Every procedure claim must match shipped behavior:
   - capture only in an `open` campaign, including a reactivated one;
   - `e000` for no encounter;
   - narratives required for canonize and note;
   - archive only after a disposition;
   - no delete and no formal lore links.
4. Make no code changes. Run the full suite, including the `test_docs` size cap and repository-name leak guard.

## Verification

- `pdm run pytest -q` passes, including `tests/core/test_docs.py`: the guide is at most 45,000 characters, and no repository campaign or encounter names leak, `e000` excepted. No skips or deletions are added to dodge failures.
- `pdm run ruff format .` has been applied, and then `pdm run ruff check .` and `pdm run ruff format --check .` are clean.
- `docs_get("workflow")` (or `cac docs get workflow`) returns the updated guide and fits the docs response budget.
- **Internal consistency:** a full-guide search for "REJECT", "NOT-REVIEWABLE", "reviewed", "gate", "override", "rumor" and "ruling" finds no statement that contradicts the new procedure. Specifically:
  - the Codex handoffs paragraph and lifecycle step 5 include the override path;
  - the gates text says a REJECT override is the developer's draft-to-reviewed approval and that gate 2 still applies;
  - Ownership and Capture rulings agree on who captures.
- Reading the diff against b005 and the shipped tools confirms:
  - each of the five edits is present;
  - no statement contradicts e001–e003 behavior (capture guard, lifecycle, archival independence, prime and search);
  - `tool-reference.md` needs no change.
