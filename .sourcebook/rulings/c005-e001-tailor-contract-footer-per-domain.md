---
archived: false
campaign: c005-clean-tool-descriptions
created_by: John Hoff
created_on: '2026-11-21T15:52:04Z'
encounter: e001-clean-tool-descriptions
history: []
name: c005-e001-tailor-contract-footer-per-domain
origin: John Hoff (GM), answering b007's open question while drafting c005/e001
resolution: null
status: recorded
summary: 'Tailoring the identity-contract footer per domain is in scope for c005:
  the "Qualified encounter context overrides active fallback..." sentence appears
  only on encounter-domain tools and commands, not boss, campaign or rumor ones, with
  tool-reference.md updated to match. This overrides b007''s "contract text unchanged"
  criterion for that one sentence.'
updated_by: John Hoff
updated_on: '2026-11-21T15:52:04Z'
---

## Decision

Tailor the shared reference-contract footer in c005/e001 rather than capturing it as a separate rumor: emit the qualified-encounter-context sentence only for the encounter domain (including `prime_applicable_lore`), leaving every other footer sentence and the ruling footer unchanged.

## Context

b007 left open whether tailoring the footer, noted but not changed in c004/e002, was in scope. Its success criteria said the contract text stays unchanged and `tool-reference.md` needs no update unless it does. The recommended option was a separate rumor; the developer chose to include it.

## Consequences

- b007's "contract text unchanged" criterion is deliberately relaxed for this one sentence; all other criteria stand.
- `tool-reference.md`'s Short references section must document the domain-specific footer (`workflow-doc-source-of-truth`).
- A test asserts which domains carry the sentence.
