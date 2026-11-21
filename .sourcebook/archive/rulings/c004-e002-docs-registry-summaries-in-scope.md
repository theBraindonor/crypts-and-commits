---
archived: true
campaign: c004-tool-description-accuracy
created_by: John Hoff
created_on: '2026-11-21T06:11:05Z'
encounter: e002-description-drift-sweep
history:
- action: note
  by: John Hoff
  message: Noted during planning triage on 2026-11-21. This was a scope exception
    for c004/e002 alone, allowing wording fixes to the core/docs.py registry summaries.
    It was never exercised, because the audit found the registry summaries accurate.
    It sets no lasting convention, so no lore, region or world change is needed.
  'on': '2026-11-21T06:25:01Z'
name: c004-e002-docs-registry-summaries-in-scope
origin: Developer (GM), resolving c004/e002 review note (b) before opening
resolution: Noted during planning triage on 2026-11-21. This was a scope exception
  for c004/e002 alone, allowing wording fixes to the core/docs.py registry summaries.
  It was never exercised, because the audit found the registry summaries accurate.
  It sets no lasting convention, so no lore, region or world change is needed.
status: noted
summary: The descriptive summary strings in the core/docs.py docs registry are in
  scope for c004/e002's wording-only drift fixes, although they live in core/. They
  are agent-facing text shown by docs_list and docs_get, not logic. This relaxes e002's
  Verification rule that only docstrings, help strings, packaged doc/template text
  and tests change.
updated_by: John Hoff
updated_on: '2026-11-21T06:25:06Z'
---

## Decision

Wording-only corrections to the `summary` strings in the `_DOCS` registry of `packages/crypts-and-commits/src/cac/core/docs.py` are permitted within c004/e002. The developer chose this over capturing such drift as a rumor.

## Context

The independent review of c004/e002 (PASS-WITH-NOTES, note b) observed that `docs_list` and `docs_get` surface registry summaries that are stored in `core/docs.py`. That makes them agent-facing descriptions, but editing them would technically break e002's Verification rule ("`git diff` shows only docstrings, help strings, packaged doc/template text and tests").

## Consequences

- e002's diff may include changes to `core/docs.py` registry summary strings. Registry names, paths, ordering and logic stay unchanged.
- Other `core/` changes remain out of scope for e002.
