# Context Management Design

Status: **design / pre-implementation.** This document captures the design
reasoning for how a coding assistant retrieves `.sourcebook` context — today via
chained CLI calls, in future via an MCP server. It is written to be durable
*before* the work is broken into actionable encounters. It records decisions and
their rationale, and explicitly flags the decisions still open.

## Problem statement

Priming context from `.sourcebook` today is a chain of many small CLI calls
(mostly `Bash` shelling out to `cac`): `cac world get`, then `cac lore list`,
then `cac lore get <name>` per entry, then `cac region get <region>` and its
lore, and so on. The pain is **round-trip count**, not (yet) payload size.

As the MCP interaction layer is designed to replace those shell-outs, we want to
choose retrieval patterns deliberately, informed by a prior lesson: in an earlier
RAG-style project, returning *everything* through a single MCP document-search
call hit the interaction character limit. The naive fix — "return it all" — does
not scale.

## Guiding distinction: two different retrieval problems

The earlier RAG failure and the `.sourcebook` churn are **not the same problem**,
and conflating them leads to the wrong pattern:

- **Relevance-ranked search** — an unbounded corpus, ranked by relevance, where
  you cannot know ahead of time which hits matter. "Return everything" fails
  because the result set has no natural bound.
- **Deterministic graph traversal** — a small, bounded, structured, *relational*
  dataset. Given an encounter, the set of applicable lore is *computable*, not
  ranked. The cost here is round-trips, not payload.

Most `.sourcebook` retrieval is the second kind. The RAG two-call pattern is the
right tool only for the (currently hypothetical) first kind.

## Patterns and where each applies

### 1. Deterministic aggregation (the common case)

Do not expose primitive CRUD over MCP and force the agent to re-chain it — that
just moves the bash chain into MCP calls and re-pays tool-call overhead per hop.
Instead expose **one call per agent intent** that performs the traversal
server-side and returns the assembled bundle. Examples:

- `context_prime(region?)` → world summary + applicable world lore + region doc
  + region lore, in one call.
- `encounter_applicable_lore(encounter, campaign?)` → the exact resolved lore set
  a reviewer needs (world-assigned enabled ∪ region-assigned enabled) — the
  reviewer subagent's priming step collapsed to one round trip.

This aligns with the project's long-term goal (see `CLAUDE.md`) that the agent
eventually has *no awareness of `.sourcebook`'s existence*: that is only
achievable if the MCP surface is shaped around **intents**, not files.
File-CRUD-over-MCP leaks the storage model straight back into the agent.

### 2. Relevance-ranked search (future / the numerous corpus)

For a genuinely large or unbounded corpus — in CAC, that means **encounters**,
not lore/region/world — use the **two-call pattern**:

- `search(query, limit)` → `[{ref, score, snippet}]` — references, relevance
  scores, and a short snippet, **never full bodies**.
- `get(ref)` → hydrate only the specific hits the model chose.

Refinements that matter:

- **Snippets** in the search result let the model often decide *without*
  hydrating at all.
- **Scores** let the model self-limit ("only the top 2 look relevant").
- Avoid the anti-pattern where the model almost always hydrates all N hits
  anyway — then the split has only *added* a round trip per doc. Snippets +
  scores are what prevent that.

Lore/region/world stay **out** of search — they are bounded and resolved by
assignment, not relevance. Mixing them in would reintroduce the RAG shape where
it does not belong.

### 3. Progressive disclosure + budget (the invariant that prevents the wall)

The character-limit wall is prevented by making the budget a **server-side
guarantee**, not something we hope stays small:

- **Summaries/frontmatter by default, bodies on request.** A `list` returns
  `name + one-line summary + status/assignment`, never bodies.
- **A token/char budget per response**, and when it truncates, say so explicitly
  with a cursor: `{ items: [...], next_cursor: "...", truncated: true }`.

The explicit-truncation point is the core lesson from the earlier project:
returning "everything" risks *silent* client-side truncation, which is worse
than paging because neither side can tell it happened.

## Write-time materialization of summaries

The key scaling decision. Deterministic aggregation alone does not survive growth
— `context_prime` returning all applicable lore *bodies* grows linearly with lore
count. The fix is to move summarization from **read time** (every encounter,
frequent) to **write time** (every lore/world/region edit, rare) and store the
result. This is a precomputed projection / materialized view.

It fits CAC especially well for two reasons:

1. **We own the write path.** Every write goes through `cac`/MCP, so summary
   regeneration can be a *mandatory step of the edit transition*, wired into the
   same hook that already stamps `updated_on`/`updated_by`. The summary can be
   **guaranteed never stale** relative to its body — a guarantee general RAG
   cannot make.
2. **The read:write ratio is lopsided and grows more so** — more encounters per
   unchanged lore item over time. That is exactly the profile where
   precomputation wins.

### Tiered read model

Only the cheapest thing stays live:

| Tier | Computed when | Why |
|---|---|---|
| **Selection** — *which* lore/region applies | Live, at read | Assignments change; cheap graph traversal; must be current |
| **Summary** — bounded précis of each object | Precomputed at write | Expensive/large; changes rarely |
| **Body** — full normative text | On demand, per item | Only pulled when a specific item needs exact text |

`encounter_applicable_lore` resolves the finite applicable set live, returns
`[{name, summary, ref}]` within budget, and the caller hydrates specific `ref`s
only when it needs exact text. Because the set is deterministic, the caller knows
exactly the finite list to hydrate — no ranking, no search.

### Critical caveat: lore is governance, not orientation

Lore is the standard a reviewer subagent checks a plan *against*. A summary is
perfect for the **breadth/orientation pass** ("what standards exist, roughly").
It is **dangerous as the sole basis for a compliance verdict**, because a lossy
or smoothed summary of a rule can cause the reviewer to miss a real conflict.

Rule to bake in: **summaries drive selection and breadth; the actual per-item
review check hydrates the full body.** The precomputed summary must not silently
become the source of truth in the review gate. The reviewer flow becomes: "here
are the N applicable lore summaries (cheap map) → hydrate each body to check the
plan against the exact rule."

## Concrete schema and prime contract

### `summary` field

- Lands on **`region` and `lore`** (the objects served without their body).
- **World** needs none — served full, and `world.md` is already a summary of
  purpose by definition. **Campaign** needs none — its body is served full.
- Stored in **frontmatter**, kept **short and length-capped**. The cap is what
  makes the primed payload *predictable*. If a summary must run to a paragraph, a
  delimited `## Summary` section the tool extracts is preferable to a YAML block
  scalar — but the default is a short capped frontmatter field.

### Global prime bundle

> **Global prime** = world (full) + world-assigned lore (summaries) + region map
> (per region: `summary` + `path` + assigned-lore *edge names*) + active campaign
> (full body).

Notes:

- **World-assigned (always-on) lore** applies to every encounter — its
  *summaries* belong in the global prime. Region-specific lore summaries do
  **not**; they wait for region focus.
- The region map carries **edges only** at global scope (which lore attaches to
  which region, by name) — not the lore summaries themselves.
- "Active campaign full" = the campaign **body**, *not* its encounters. The
  encounter list under a campaign is a separate, paged, on-demand call — never
  part of prime. It is the thing that grows without bound.
- The same budget/paging invariant applies to the region map itself at extreme
  scale (many regions).

### Disclosure ladder

The **procedure** for going deeper lives in the **skill instructions** (static —
authored once), not in the tool response. Re-sending traversal prose in every
prime call is exactly the per-call token churn we are avoiding. The tool returns
only the **data traversed on** (the region→lore edges); the "how" is authored
once in the skill.

| Step | Payload | Source |
|---|---|---|
| Orient | world full + world-lore summaries + region map + campaign body | one `context_prime` call |
| Focus a task | region full + that region's lore summaries | `region_get` / region-lore call |
| Review a plan | full lore bodies for the applicable set | hydrate specific `ref`s |

## Skill ownership split

The pattern maps cleanly onto the existing two skills:

- **`world-manager`** owns the static substrate (world/region/lore): deterministic
  aggregation, summary maintenance, and the `context_prime` operation. Small,
  bounded, resolved by graph — never search.
- **`campaign-manager`** owns the active loop, and **freeform search belongs
  here**, because the numerous/freeform corpus is *encounters*. This is the one
  place the two-call `search → hydrate` pattern earns its keep.

One correction to a clean split: **priming crosses the boundary.** The global
prime includes the active campaign (a campaign-manager object). So priming is not
*exclusively* world-manager. The model: world-manager *provides* the static
prime; campaign-manager *invokes* it as step one of any work and appends the
active-campaign context. This already reflects how the skills interlock today
("prime with world-manager, then check encounters with campaign-manager") — the
MCP contract just formalizes it.

## Open decisions (to resolve before / during breakdown)

1. **How summaries are produced.** Options: (a) **authored** frontmatter field;
   (b) **generate-and-approve** (tool drafts at edit time, GM approves before
   commit); (c) auto-generate with no gate. Leaning **(a) authored, optionally
   generation-assisted** for v1 — cheapest, highest trust, and for lore (a
   governance artifact) an unreviewed summary is a silent single point of failure
   in the review pipeline. "Auto-generate, no gate" is discouraged for lore.
2. **Summary length cap.** The concrete cap that makes primed payload
   predictable. Drives the write-time hook and the budget math.
3. **Frontmatter field vs `## Summary` section** as the storage location for the
   longer-summary case (default is a short capped frontmatter field).
4. **Budget/cursor mechanics** for list and map responses (page size, truncation
   signaling shape).

## Summary of decisions converged on

- Separate **deterministic traversal** (aggregate server-side) from
  **relevance-ranked search** (two-call refs→hydrate); apply each only to its
  matching domain.
- Add a capped **`summary`** frontmatter field to **region and lore**;
  **materialize it at write time**, enforced on the edit transition, guaranteeing
  it is never stale.
- Serve a **tiered read**: live selection → precomputed summary → body on demand.
- For **lore specifically**, summaries **route**; **bodies remain ground truth**
  for the review gate.
- **Global prime** = world full + world-lore summaries + region map + active
  campaign body; the traversal *procedure* lives in the **skill**, not the tool
  payload.
- **world-manager** owns static aggregation + prime; **campaign-manager** owns the
  active loop + encounter search and *invokes* prime.
