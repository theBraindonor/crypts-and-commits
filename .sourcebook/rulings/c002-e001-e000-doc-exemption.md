---
archived: false
campaign: c002-rulings
created_by: John Hoff
created_on: '2026-11-21T02:20:48Z'
encounter: e001-ruling-records-core
history: []
name: c002-e001-e000-doc-exemption
origin: Developer (GM), during c002/e001-ruling-records-core execution
resolution: null
status: recorded
summary: Exempt the reserved e000 marker from the paired-docs leak guard regex instead
  of writing around it in the shipped guides. e000 is a sentinel agents need to see,
  not a repository encounter name.
updated_by: John Hoff
updated_on: '2026-11-21T02:20:48Z'
---

## Decision

Narrow the regex in `test_paired_docs_ship_no_repository_campaign_or_encounter_names` with a `(?!e000)` lookahead, so that `workflow.md` and `tool-reference.md` can write `e000` literally.

## Context

The test bans tokens like `c0NN` and `e0NN` from the paired docs, so names of this repository's own campaigns and encounters don't leak into the guides shipped to other projects. Ruling names use `e000` as the reserved "no encounter" marker, and agents need to see it to record campaign-level rulings. The alternative was to describe it indirectly, for example as "encounter number zero". That was rejected because the docs would be less direct.

## Consequences

The leak guard still catches every other `c0NN`/`e0NN` token. `e000` can never be a real encounter, because encounter numbers start at 001, so the exemption can't hide a leaked repository name.
