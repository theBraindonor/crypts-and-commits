---
archived: true
campaign: v0.1.7-rag-demo-application
created_by: John Hoff
created_on: '2026-08-06T14:49:55Z'
depends_on: []
name: add-chat-persona-and-context-priming
regions:
- demo-api
status: completed
updated_by: John Hoff
updated_on: '2026-08-09T14:09:04Z'
---

# Add chat persona and context priming

## Requirements

- The chat agent's system prompt must convey a defined persona: a friendly assistant whose purpose is to help with and answer questions about the current sourcebook project (this repository, Crypts and Commits / "CAC") — replacing the current generic `"You are a friendly assistant."`.
- Immediately after the persona system prompt, and before the placeholder carrying prior conversation turns, the prompt must include the project's standard context-priming content: the same "Orient" bundle the `world-manager` skill's disclosure ladder describes as step 1 — world summary, world-assigned enabled lore summaries, region map, and the active campaign's body — so the agent has this project's live world-building context available when answering.
- The priming content must be sourced by calling the `cac` package's `core` layer directly — `cac.core.prime.assemble_prime`, the same function `mcp/prime.py`'s `prime_get` tool wraps — not the MCP server and not a `cac` CLI subprocess. `demo-api` is ordinary Python application code living in the same PDM workspace, not an agent session; the `.sourcebook`-is-MCP/CLI-only guardrail governs coding-assistant sessions editing `.sourcebook`, not this read-only library call from application code.
- This is a read-only read of `.sourcebook` content — no write path is introduced, consistent with the wider `v0.1.7-rag-demo-application` campaign's read-only requirement for the demo application.
- Existing chat plumbing (streaming, thread/checkpoint handling, model selection, the `/chat` request/response contract) is unchanged.

## Rationale

This is the next incremental step in the `demo-api` region ahead of wiring RAG-proper (`index_search`) into the agent: giving the chatbot an explicit persona plus this project's own world/lore/region/campaign context grounds its answers in the actual sourcebook, rather than answering as a generic assistant with no project awareness.

Calling `cac.core.prime.assemble_prime` directly (rather than shelling out to the CLI or going through the MCP server) reuses the exact same read-only logic the CLI and MCP tool already wrap, avoids spawning a subprocess or an MCP client from inside a FastAPI request/startup path, and is the natural choice for same-workspace Python application code — `demo-api` already sits in this PDM workspace alongside `crypts-and-commits`.

Computing the priming text once at graph-build time (server startup, inside the `lifespan` handler) rather than per-request mirrors the existing static `SYSTEM_PROMPT` and the already-injectable `model` parameter on `build_graph` — it keeps `/chat` request latency unaffected and keeps the same testability pattern (a fake/override can be substituted for tests) already established for `model`.

## Plan

1. Add `"crypts-and-commits"` to `demo-api`'s `[project].dependencies` in `packages/demo-api/pyproject.toml` so PDM's workspace resolution wires it to the local editable package; run `pdm lock` and `pdm install` afterward.
2. In `packages/demo-api/src/demo_api/chat/config.py`, add `REPO_ROOT = DEMO_API_ROOT.parent.parent` alongside the existing `DEMO_API_ROOT` — the directory containing `.sourcebook` (this repository's root).
3. Add a new module `packages/demo-api/src/demo_api/chat/priming.py` with a `render_context_priming(root: Path) -> str` function that calls `cac.core.prime.assemble_prime(root)` and renders the returned `PrimeBundle` into a single plain-text block: the world's name and body, a bulleted list of world-assigned lore (name + summary), a bulleted list of regions (name, path, summary), and the active campaign's name and body — formatted for inclusion as prompt content.
4. In `packages/demo-api/src/demo_api/chat/graph.py`:
   - Replace `SYSTEM_PROMPT` with persona text, e.g.: `"You are the Crypts and Commits project assistant: a friendly, knowledgeable guide who helps developers understand this project and answers questions about its current sourcebook - world context, lore, regions, and campaigns."`
   - Give `build_graph` an optional `priming: str | None = None` parameter (mirroring the existing `model: BaseChatModel | None = None` override), defaulting to `priming.render_context_priming(REPO_ROOT)` when not passed.
   - Build the `ChatPromptTemplate` with, in order: `("system", SYSTEM_PROMPT)`, then a message carrying the priming content as a `system`-role entry (project context, not a user turn), then `MessagesPlaceholder("messages")` — preserving "follows the prompt, appears before the chat messages" ordering.
5. Add tests:
   - A focused test for `render_context_priming` confirming it surfaces the world's name/body, using this repo's own real `.sourcebook` (consistent with the project dogfooding itself).
   - A test that `build_graph(..., priming="<marker text>")` produces a `ChatPromptTemplate` whose formatted messages include the persona text and the injected priming text, in that order, ahead of the conversation placeholder — verified by formatting the underlying prompt template directly rather than relying on the fake chat model.
6. Run `pdm run pytest -q` and `pdm run ruff check .` / `pdm run ruff format .`; fix anything either surfaces.

## Verification

- `pdm run pytest -q` passes with no skips or deletions used to dodge a failure — existing `test_chat.py` tests keep passing unmodified in behavior (thread/streaming plumbing is untouched), and the new tests from step 5 pass.
- `pdm run ruff check .` reports zero errors and `pdm run ruff format .` reports no diffs.
- Manual smoke check (not part of automated verification): start the API from `packages/demo-api` and `POST /chat`, confirming the reply reflects the assistant persona and that priming content reached the model — e.g. asking "what is this project?" produces an answer referencing Crypts and Commits.

## Log

### Review - 2026-08-06T14:54:59Z - John Hoff

Reviewed against the one applicable lore item resolved by prime_applicable_lore (world-assigned clean-tests-and-lint; the demo-api region carries no region-specific lore) — the Plan's step 6 and Verification section explicitly run and require a clean `pdm run pytest -q` and `ruff check`/`format`, matching the lore's gate exactly, with no skip/--no-verify/# noqa shortcuts proposed. Spot-checked the Plan's file-level claims against packages/demo-api/src/demo_api/chat/config.py, graph.py, and pyproject.toml: DEMO_API_ROOT.parent.parent correctly resolves to the repo root, the existing SYSTEM_PROMPT/ChatPromptTemplate/build_graph(model=...) pattern the Plan says it will mirror is present as described, and crypts-and-commits is indeed not yet a demo-api dependency. Two points are flagged as unverified rather than checked, being outside the prescribed priming surface: the Plan's reference to the parent campaign's "read-only requirement" (campaign body not fetched), and the Plan's own interpretation that a direct cac.core.prime.assemble_prime call from demo-api application code falls outside the .sourcebook-is-MCP/CLI-only guardrail (that guardrail isn't an enabled/assigned lore entry in this project, so it wasn't part of the lore set graded here). PASS-WITH-NOTES.

### Message - 2026-08-06T14:59:28Z - John Hoff

Added and assigned lore `demo-api-uses-cac-core-directly` to the `demo-api` region, codifying that demo-api interacts with .sourcebook data by calling cac.core.* functions directly (e.g. cac.core.prime.assemble_prime) rather than the cac CLI or MCP server, and that these calls must stay read-only. This confirms, as region-assigned lore rather than just this encounter's own Plan/Rationale text, the approach the reviewer flagged as unverified (its interpretation of the .sourcebook-is-MCP/CLI-only guardrail not applying to same-workspace application code). Created after this encounter's Plan was already reviewed and locked, so it did not retroactively change the review verdict, but the locked Plan already follows it.

### Message - 2026-08-06T15:10:18Z - John Hoff

Implementation deviation worth recording: Plan step 1's `pdm lock` (plain, no strategy flag) did a full re-resolution and unexpectedly bumped the unrelated `mcp` SDK dependency from 1.28.1 to 2.0.0, which broke `cac.mcp.instance`'s `from mcp.server.fastmcp import FastMCP` import (removed/moved in 2.0.0) and made every `cac.mcp.*` test fail to collect. Fixed by reverting pdm.lock and re-running `pdm lock --update-reuse`, which only resolves the new demo-api -> crypts-and-commits edge and keeps every other pin, including mcp at 1.28.1. Also noted: `pdm install` cannot fully complete in this dev environment while a `crypts-and-commits` MCP server session is running, since it holds `cac-mcp.exe`/`cac.exe`'s console-script shims open on Windows (PermissionError on overwrite) - the actual package installs/imports succeed regardless (verified directly), only the entry-point script regeneration fails; this is a pre-existing environment quirk, not something this encounter's changes caused.

Verification complete: `pdm run pytest -q` -> 773 passed. `pdm run ruff check .` -> clean. `pdm run ruff format --diff .` -> no diffs. Manual smoke check: started the API (uvicorn on port 8756) and POSTed to /chat asking "What is this project?" - the streamed reply correctly described Crypts and Commits (CAC), the tabletop-gaming metaphor, Game Master role, and the sourcebook, confirming persona + priming both reached the model in the intended order. Server stopped afterward.

### Message - 2026-08-06T15:47:51Z - John Hoff

Stopgap fix applied at the user's direction, outside this encounter's own Plan scope but recorded here since it was triggered by this encounter's `pdm lock` work: pinned `mcp<2.0.0` in `packages/crypts-and-commits/pyproject.toml` (was unpinned) to stop future `pdm lock` runs from repeating the 1.28.1 -> 2.0.0 jump that broke `cac.mcp.instance`'s `fastmcp` import (confirmed by downloading the 2.0.0 wheel in isolation: `fastmcp` is absent from it entirely, not just moved). Relocked with `pdm lock --update-reuse` (mcp stays 1.28.1) and re-verified: `pdm run pytest -q` -> 773 passed, `ruff check`/`format` -> clean. A follow-up draft encounter is being added to the release-readiness campaign to properly upgrade to the latest mcp release and put better version-pinning practice in place workspace-wide - this was only the minimal pin needed to stop the bleeding.

### Completed - 2026-08-06T15:47:55Z - John Hoff

Persona and context priming shipped and verified: chat agent now opens with a Crypts and Commits persona followed by a cac.core.prime.assemble_prime-sourced priming message before the conversation placeholder. pdm run pytest -q (773 passed) and ruff check/format clean; manual /chat smoke test confirmed grounded answers. Stopgap mcp<2.0.0 pin applied alongside this work to stop pdm lock from repeating the breaking 2.0.0 jump; proper mcp upgrade + wider version-pinning cleanup deferred to a new release-readiness encounter.
