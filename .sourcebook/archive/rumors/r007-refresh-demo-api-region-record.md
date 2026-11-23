---
archived: true
boss: null
created_by: John Hoff
created_on: '2026-11-23T17:33:05Z'
history:
- action: dismiss
  by: John Hoff
  message: Resolved directly on planning, 2026-11-23, with developer approval; no
    goal needed. The demo-api region's summary and body were refreshed via region_update
    to describe the current persona, live sourcebook priming, literal SystemMessage
    prompt construction, the read-only cac.core tool set (including search_sourcebook),
    NDJSON streaming and SQLite checkpointing. Still to confirm now covers only demo-ui
    consumption of /chat and any retrieval beyond search_sourcebook.
  'on': '2026-11-23T18:14:38Z'
name: r007-refresh-demo-api-region-record
origin: Independent reviewer of c006/e002 (flagged as out of scope), captured at the
  developer's request on 2026-11-23
resolution: Resolved directly on planning, 2026-11-23, with developer approval; no
  goal needed. The demo-api region's summary and body were refreshed via region_update
  to describe the current persona, live sourcebook priming, literal SystemMessage
  prompt construction, the read-only cac.core tool set (including search_sourcebook),
  NDJSON streaming and SQLite checkpointing. Still to confirm now covers only demo-ui
  consumption of /chat and any retrieval beyond search_sourcebook.
status: dismissed
summary: The demo-api region record (summary and body, last updated 2026-08-06) is
  stale. It still describes the system prompt as "You are a friendly assistant." and
  says there are no tools, but the code now has a CAC project-assistant persona, sourcebook
  context priming via cac.core, read-only sourcebook lookup tools, and (since c006/e002)
  literal SystemMessage prompt entries. Refresh the summary and body to match.
updated_by: John Hoff
updated_on: '2026-11-23T18:14:42Z'
---

## Observation

The `demo-api` region record (`packages/demo-api`, last updated 2026-08-06) no longer matches the code:

- **System prompt.** The summary and body say the prompt starts from "You are a friendly assistant." `graph.py::SYSTEM_PROMPT` is now a Crypts and Commits project-assistant persona that answers questions about the sourcebook and prefers its tools for live status.
- **Context priming.** `build_graph` adds a second system message from `render_context_priming(REPO_ROOT)` (`chat/priming.py`), which carries live sourcebook context read through `cac.core`. The region record doesn't mention it.
- **Tools.** The record says "no RAG, no tools yet" and lists tool-calling under "Still to confirm". The graph now binds tools from `chat/tools/` (docs, lore, region, world, campaigns and encounters, e.g. `list_campaigns`) with a LangGraph `ToolNode` and `tools_condition` loop. They are read-only lookups via `cac.core`.
- **Prompt construction.** Since c006/e002, `_build_prompt` passes the persona and priming as literal `SystemMessage` entries, so sourcebook braces are never treated as template variables.

## Suggested action

During planning, refresh the region's summary and body (`region_update` / `region_set_summary`) to describe the current persona, priming, tool set and prompt construction. Re-check what's still open, such as whether RAG retrieval is still planned now that priming and tools exist, and how demo-ui consumes `/chat`. Developer approval is needed for the new text.

## Origin

Flagged by the independent reviewer of c006/e002 as out of scope for that encounter, and captured at the developer's request.
