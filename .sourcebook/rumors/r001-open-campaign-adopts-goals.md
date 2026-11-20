---
archived: false
boss: b003-sourcebook-integrity
created_by: John Hoff
created_on: '2026-10-28T17:53:40Z'
history:
- action: promote
  by: John Hoff
  message: 'Planning 2026-11-20: developer folded goal adoption into the shared sourcebook-integrity
    goal with r002.'
  'on': '2026-11-20T23:43:35Z'
name: r001-open-campaign-adopts-goals
origin: 'c001-boss-edition dogfooding, 2026-10-28: linking b001/b002 to the already-open
  c001 needed a GM override (hand-edited bosses/campaign frontmatter), recorded in
  c001/e025.'
resolution: 'Planning 2026-11-20: developer folded goal adoption into the shared sourcebook-integrity
  goal with r002.'
status: promoted
summary: Let an open campaign adopt existing unassigned goals (or recorded in-progress
  roadmap goals) so its completion vanquishes them, instead of requiring a developer
  hand-edit of campaign and boss frontmatter.
updated_by: John Hoff
updated_on: '2026-11-20T23:43:35Z'
---

Campaign boss membership can only change while a campaign is `draft` (`campaign_set_bosses`), and `boss_record` never links a recorded goal to a campaign. A campaign that opened before its goals existed as bosses, which is common for a project's first Boss Edition campaign or for legacy open work, has no supported way to own them. Completing it vanquishes nothing.

The workflow already names this gap ("adopting ownership into an already-open legacy campaign is deferred"). A guarded adoption operation could close it, for example `campaign_adopt_bosses(name, bosses, message)` on an open or paused campaign. It would require a reason, log the change in the campaign, validate reciprocal ownership and eligibility, and stay CLI/MCP-parity compliant.

Open questions: should adoption require prerequisite eligibility as selection does, or allow co-adopted prerequisites? Should it be limited to the first campaign or to legacy campaigns? How does it interact with the freeze rule for designs and with reactivation?
