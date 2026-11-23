---
archived: true
campaign: c006-applicable-lore-mcp-paging
created_by: John Hoff
created_on: '2026-11-21T17:15:21Z'
encounter: e001-applicable-lore-mcp-paging
history:
- action: canonize
  by: John Hoff
  message: 'Canonized into lore cli-mcp-parity (crypts-and-commits region) with developer
    approval on planning, 2026-11-23. A new paging bullet requires every new or changed
    paged MCP result to fit the response budget as emitted: items sized as compact
    JSON, the full envelope reserved, and one core paging helper shared with the CLI
    so page breaks match, with a single oversized item as the only allowed overrun.
    The summary was updated to match. The ruling''s consequence that the other plain
    lists keep looser measurement was captured as rumor r008-json-measure-plain-list-paging.'
  'on': '2026-11-23T18:14:32Z'
name: c006-e001-json-measured-applicable-lore-paging
origin: John Hoff (GM), responding to the c006/e001 reviewer REJECT
resolution: 'Canonized into lore cli-mcp-parity (crypts-and-commits region) with developer
  approval on planning, 2026-11-23. A new paging bullet requires every new or changed
  paged MCP result to fit the response budget as emitted: items sized as compact JSON,
  the full envelope reserved, and one core paging helper shared with the CLI so page
  breaks match, with a single oversized item as the only allowed overrun. The summary
  was updated to match. The ruling''s consequence that the other plain lists keep
  looser measurement was captured as rumor r008-json-measure-plain-list-paging.'
status: canonized
summary: 'Applicable-lore paging is measured on compact JSON, not the CLI text line:
  a shared core/prime.py helper sizes each {name, summary, ref} item as compact JSON
  with headroom for the {items, next_cursor} envelope, and both MCP and CLI page with
  it, so page breaks match and every MCP page fits the response budget. Empty-set
  cursor behavior is pinned on both surfaces. Chosen over amending the docs or a GM
  override.'
updated_by: John Hoff
updated_on: '2026-11-23T18:14:40Z'
---

## Decision

Revise c006/e001 so `prime_applicable_lore` and `cac prime applicable-lore` page with one shared core helper that measures each entry's compact JSON plus envelope headroom, instead of the CLI's text line. `tool-reference.md` states that applicable-lore pages are JSON-measured. Tests pin that an out-of-range cursor fails on both surfaces, even when no lore applies.

## Context

The independent reviewer rejected e001 because text-line measurement lets an MCP JSON page exceed the response budget, contrary to `tool-reference.md`'s budget contract (`cli-mcp-parity`, `workflow-doc-source-of-truth`). On inspection the contract's compact-JSON wording strictly covers `get` responses and identity-bearing lists, and the plain lists (`lore_list`, `region_list`, `docs_list`) measure looser renderings, but the overrun risk is real. The alternatives were to amend `tool-reference.md` to document text-line measurement for plain lists, or a GM override citing that precedent; the developer chose the JSON measurement.

## Consequences

- MCP pages of applicable lore always fit the response budget.
- CLI page breaks shift slightly (fewer entries per page). That is internal, and the CLI and MCP stay identical to each other.
- The CLI validates the cursor before reporting that no lore applies, a small behavior change pinned by tests.
- Other plain lists keep their current measurement; aligning them would be separate work.
