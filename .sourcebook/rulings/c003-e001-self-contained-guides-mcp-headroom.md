---
archived: false
campaign: c003-workflow-guide-split
created_by: John Hoff
created_on: '2026-11-21T04:59:46Z'
encounter: e001-workflow-split-design
history: []
name: c003-e001-self-contained-guides-mcp-headroom
origin: Developer (John Hoff), joint review of c003/e001 design comparison
resolution: null
status: recorded
summary: Choose two self-contained phase guides with consistent shared duplication,
  retaining workflow as a short index and no common-workflow guide initially. The
  40,000-character cap primarily supports broad compatibility with MCP call character
  limits; eliminating duplication is secondary.
updated_by: John Hoff
updated_on: '2026-11-21T04:59:46Z'
---

## Decision

The developer accepted Candidate A: self-contained planning-workflow and development-workflow guides, with consistent shared duplication and workflow retained as a short routing entry point. Do not extract a common-workflow guide initially.

## Context

The design comparison estimates about 30,325 and 31,277 characters including wrapper allowances, below the 40,000-character cap. The developer explicitly accepted the duplication and clarified that keeping guides short is primarily about character limits imposed on MCP calls and seeking the broadest support.

## Consequences

Enforce the cap independently for each workflow guide. Prefer complete, logically consistent phase guidance over eliminating duplication. The compatibility objective is headroom across MCP clients, not a claim that every client has the same limit or that all clients have been tested. Joint logical review and clean automated checks support campaign completion; later practical usage remains organic. This design decision does not bypass any follow-up encounter's review, opening or completion gates.
