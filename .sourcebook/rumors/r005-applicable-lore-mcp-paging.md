---
archived: false
boss: b008-applicable-lore-mcp-paging
created_by: John Hoff
created_on: '2026-11-21T06:13:46Z'
history:
- action: promote
  by: John Hoff
  message: Promoted during planning triage on 2026-11-21 with developer approval.
    The MCP/CLI paging asymmetry is unintended and violates cli-mcp-parity; captured
    as b008-applicable-lore-mcp-paging.
  'on': '2026-11-21T16:11:04Z'
name: r005-applicable-lore-mcp-paging
origin: c004/e002 description drift sweep
resolution: Promoted during planning triage on 2026-11-21 with developer approval.
  The MCP/CLI paging asymmetry is unintended and violates cli-mcp-parity; captured
  as b008-applicable-lore-mcp-paging.
status: promoted
summary: prime_applicable_lore over MCP takes no cursor and returns the whole applicable-lore
  list unpaged, while cac prime applicable-lore pages with --cursor. The world-manager
  skill had documented an MCP cursor. Decide whether the MCP tool should gain cursor
  paging for CLI/MCP parity and budget safety, or whether unpaged MCP is intended.
updated_by: John Hoff
updated_on: '2026-11-21T16:11:04Z'
---

## Observation

- `mcp/prime.py::prime_applicable_lore(encounter, campaign=None)` returns a plain list of `{name, summary, ref}` with no `cursor` parameter and no budget paging.
- `cac prime applicable-lore NAME [-c] [--cursor]` pages under the response budget.
- `tool-reference.md` documents exactly this asymmetry. Both world-manager skill templates documented an MCP `cursor` argument and paging, which c004/e002 corrects to match the code.

## Question

Is the asymmetry intended? If not, should the MCP tool gain `cursor` paging (and a `next_cursor` result) so a large applicable-lore set can't exceed the response budget, matching every other list-shaped MCP read and the `cli-mcp-parity` lore? That would be a behavior/contract change, so it was out of scope for c004's wording-only pass.
