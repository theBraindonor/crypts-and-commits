---
archived: false
campaign: c001-boss-edition
created_by: John Hoff
created_on: '2026-10-28T17:54:01Z'
depends_on:
- e024-align-guides-and-repo-instructions-with-standalone-rumors
kind: unscripted
name: e025-record-gm-override-linking-c001-bosses
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-10-28T18:01:28Z'
---

## Requirements

Record a developer (Game Master) override that gave the already-open campaign c001-boss-edition two linked goals, so that completing c001 vanquishes them through the normal coupled lifecycle. Work done on 2026-10-28, on the c001 execution branch:

1. **Bosses created through MCP** (world-planner):
   - `b001-boss-records`: Boss Edition core (boss records and lifecycle, candidates, roadmap recording, numbered names and short refs, promotion and coupling, prime/search, planning skill, branch workflow and guides, CLI/hook quality-of-life).
   - `b002-rumor-records`: standalone `rNNN` rumors.
   - `b002` was given a prerequisite on `b001`, because rumor promotion targets bosses. Both were marked `available`.
2. **Ownership linked by a developer hand-edit** of managed frontmatter. The supported operations cannot do this for an open campaign: `campaign_set_bosses` works only on drafts, and `boss_record` never links. The developer set `bosses: [b001-boss-records, b002-rumor-records]` on c001 and `campaign: c001-boss-edition` on each boss, leaving both at `status: available` and `archived: false`. The assistant did not touch the files; it supplied the exact fields that `core/coupling.py` `Links._pair` validates for an open campaign.
3. **Index rebuilt.** The developer ran `cac index rebuild` (109 items).
4. **Link verified through MCP:**
   - `prime_get` lists both as active bosses with no `active_boss_diagnostics`.
   - `boss_candidates` is `healthy`, with both counted as `excluded` (assigned).
   - `index_status` is `fresh`.
5. **Rumors captured** from the same session: `r001-open-campaign-adopts-goals` (the missing supported path for this override), `r002-cascade-clean-deleted-references` and `r003-index-search-description-lists-all-types`.

The boss bodies say the override is recorded in "the c001 log and the encounter recording the override". This encounter is that record. The boss designs are now frozen, because they are linked, so that wording stays as written.

## Rationale

c001 opened bossless, because no boss records existed when Boss Edition work began. Its goals are exactly what Boss Edition delivers, and the project is dogfooding CAC: completing c001 should show the full goal-to-vanquish path for both a usage example and the next development effort. Recording the goals after the merge (`boss_record` with `progress=completed`) would give accurate provenance but no live link. Recording them now as `in_progress` would leave them `proposed` forever, because completion vanquishes only reciprocally linked bosses.

The developer judged a deliberate, logged side-step of the draft-only membership rule acceptable while actively dogfooding. The guardrail binds the assistant, not the developer, and recording it as an unscripted encounter keeps the governance exception visible and reviewable. The goals were also captured on the c001 execution branch rather than a planning branch, as an explicit first-adoption exception: no planning branch exists yet, and `main` lacks Boss Edition support until c001 merges. Future goals are to be created on planning. r001 captures the supported operation that would make this override unnecessary next time.

## Log

### Review - 2026-10-28T17:55:33Z - John Hoff

Independent lore review (unscripted record): PASS-WITH-NOTES. No source code under packages/ changed, so clean-tests-and-lint has nothing to gate, and console-best-practices and skills-authored-only-in-templates do not apply. cli-mcp-parity is honored: no command changed, and the index rebuild was run by the developer, matching its developer-only rule. workflow-doc-source-of-truth needs no doc update, because the draft-only campaign_set_bosses guard was side-stepped once by a logged developer (GM) override, not changed, and the missing supported path is captured as r001. The override is stated openly, with a reason, and is consistent with the guardrail binding only the assistant, and the planning-branch first-adoption exception is stated openly too. Notes, not verified in this review: (a) the claim that the hand-set fields satisfy coupling.py Links._pair rests on the cited prime_get, boss_candidates and index_status results; (b) the boss bodies also cite 'the c001 log', so confirm that entry exists; (c) the crypts-and-commits region is nominal, since no file under its path changed.

### Opened - 2026-10-28T17:59:13Z - John Hoff

Opened with developer approval. Follow-up from review note (b): add a GM-override note to c001's campaign body pointing to e025, so the frozen boss bodies' reference to "the c001 log" resolves.

### Message - 2026-10-28T17:59:41Z - John Hoff

Review follow-up done. (b) c001's campaign body gained a `## Log` section whose first entry, "GM override - 2026-10-28 - John Hoff", summarizes the override and points to this encounter and r001, so the frozen boss bodies' reference to "the c001 log" now resolves. Future lifecycle entries (such as the completion postmortem) append under the same section. campaign_update changed only the body; bosses stay [b001-boss-records, b002-rumor-records] and boss_link is current with no diagnostics. (a) The link evidence was rechecked through campaign_get (boss_link current, no diagnostics) in addition to the earlier prime_get/boss_candidates/index_status results. (c) Region is nominal; no action. No code changed, so there is no test or lint gate.

### Completed - 2026-10-28T18:01:28Z - John Hoff

Recorded Requirements/Rationale confirmed accurate. Review follow-up (c001 Log entry for the GM override) done and committed in 6b164d0; the c001 boss link is current with no diagnostics. Developer confirmed completion.
