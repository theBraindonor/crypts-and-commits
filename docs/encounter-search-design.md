# Encounter Search Design

Status: **deferred / design notes.** This captures what we will need to know when
we pick up encounter search. It is intentionally separated from
[`context-management-design.md`](./context-management-design.md): that document
covers *deterministic graph traversal* over the bounded static substrate
(world/lore/region) and the active campaign; this one covers *relevance-ranked
search* over the growing, freeform encounter corpus. They are different retrieval
problems and deserve different mechanics.

## Why this is a separate problem

Lore/region/world retrieval is *computable* — given an encounter, the applicable
set is resolved by graph traversal, not ranked. Encounters are the opposite: a
numerous, ever-growing, freeform body of prose where the useful hits for a query
cannot be known ahead of time. That is a search problem, and it must not be
solved by scanning-and-returning-everything (the failure mode that hit the MCP
character limit in a prior project).

Ownership: encounter search lives in the **`campaign-manager`** domain, not
`world-manager`. Lore/region/world were originally meant to stay out of search
entirely, but that call was revisited once `updated_on` existed on all three
(added by `add-created-updated-stamps-to-world-lore-region`) and reversed by
`add-world-lore-region-to-search-index`: all three are now indexed alongside
encounters. `core/search_index.py` is the current source of truth for what is
indexed today, not this paragraph.

## Requirement: a real search-engine mechanic

Search must be backed by an actual search engine / index — **not** a naive
in-process scan of every encounter body on each query. The scan approach does not
scale with the corpus and re-reads everything every time; an index is the point.

### Candidate engines (decision deferred)

- **SQLite FTS5** — zero external service, ships with Python's `sqlite3`, good
  keyword/BM25 ranking. Strong default for a local, file-backed tool.
- **Tantivy (via `tantivy-py`) / Whoosh** — richer full-text features; Whoosh is
  pure-Python but unmaintained, Tantivy is fast but adds a native dependency.
- **Vector / embedding store** — enables semantic search, but adds an embedding
  model dependency and cost, and is likely overkill for a first cut. Hybrid
  (keyword + vector) is a later option.

Leaning toward **keyword/BM25 first (SQLite FTS5)**, with semantic/hybrid as a
possible later enhancement — but this is an open decision.

## The two-call interaction pattern

Reuses the shape from the context-management design:

1. `search(query, limit)` → `[{ref, score, snippet}]` — references, relevance
   scores, and a short snippet per hit. **Never full bodies.**
2. `get(ref)` → hydrate only the specific hits the caller chooses (this is the
   existing `encounter get`).

Why: snippets let the caller often decide *without* hydrating at all; scores let
it self-limit ("only the top 2 look relevant"). This avoids the anti-pattern
where the caller hydrates all N hits anyway, which would make the split a pure
cost. Results obey the same **20,000-character response budget** and
prepend-truncation-notice behavior defined in the context-management design.

## Index-sync: tied to the write path

The index must stay current with `.sourcebook` writes. This is the *same*
write-path-ownership advantage already relied on for summaries: every encounter
write goes through `cac`/MCP, so the index can be updated on the edit transition
(create/update/review/open/record-message/complete/abandon) — the same hook that
stamps `updated_on` and (per the other doc) regenerates summaries. No stale index,
no separate reconciliation job in the common case.

Consider also:
- A **rebuild/reindex command** for cold builds and recovery (index lost,
  corrupted, or schema changed).
- Where the index lives on disk and whether it is committed or regenerated
  (likely regenerated / git-ignored, since it is derived data).

## Open decisions (for when this is picked up)

1. **Engine choice** — SQLite FTS5 (keyword/BM25) vs. a vector/hybrid store.
   Default lean: FTS5 first.
2. **What is indexed** — which fields/sections (full body, or Requirements/
   Rationale/Plan/Verification separately; frontmatter like `regions`, `status`).
   Should the `summary` field be indexed and/or returned as the snippet?
3. **Search scope** — a single campaign vs. across all campaigns; whether
   `completed`/`abandoned` encounters are included by default (history is
   valuable, but may need a flag to include/exclude).
4. **Ranking and snippet** — BM25 default; snippet as a query-highlighted excerpt
   vs. the stored `summary`.
5. **Index location & lifecycle** — on-disk path, git-ignored vs. committed,
   incremental update on the write transition plus a full reindex command.
6. **Surface** — CLI command shape now vs. exposing it only through the MCP
   `search` tool later (the MCP surface intentionally leaves a slot for this and
   does not implement it in the first cut).

## Relationship to the other encounters

Encounter search is deferred out of the initial context-management breakdown. It
has **no downstream dependents** — the summary field, tiered prime, response
budget, skill updates, and MCP surface do not read from it — so it can be built
independently, later, without reshaping any of them. The `skill-updates` and
`mcp-surface` encounters are scoped to leave a clean seam (no reference to a
search capability that does not yet exist).
