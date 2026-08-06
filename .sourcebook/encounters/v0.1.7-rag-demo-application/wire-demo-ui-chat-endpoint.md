---
archived: false
campaign: v0.1.7-rag-demo-application
created_by: John Hoff
created_on: '2026-08-06T04:28:42Z'
depends_on:
- scaffold-demo-ui-chat-app-shell
- add-streaming-chat-endpoint
name: wire-demo-ui-chat-endpoint
regions:
- demo-ui
status: completed
updated_by: John Hoff
updated_on: '2026-08-06T04:46:34Z'
---

## Requirements

- `packages/demo-ui`'s chat placeholder becomes functional: a user can type a message, submit it, and see the assistant's reply stream in incrementally (not appear all at once after the full response completes).
- Messages (both human and assistant) render in the message list area in order, replacing the "Chat coming soon." placeholder once the first message is sent.
- The frontend calls demo-api's `POST /chat` (via the existing dev-only Vite proxy, extended to cover `/chat` alongside the existing `/health` entry) with `{thread_id?, message}`, and parses the newline-delimited-JSON streamed response (`{"content": "..."}` per line) to render live as chunks arrive.
- `thread_id` is managed automatically: omitted on the first request; the value returned in the response's `X-Thread-Id` header is captured and reused for every subsequent message in the same UI session, so multi-turn conversation works without extra user action. Not persisted across page reloads (component-level React state only) - explicitly out of scope for this pass.
- Basic request/error states: the input and send control are disabled while a response is streaming in; a network or non-2xx failure surfaces a simple inline error in the message list rather than hanging silently or crashing the UI.
- No new state-management library, CSS framework, or backend changes - the `/chat` and `/health` proxy entries in `vite.config.ts` remain the same dev-only mechanism established in `scaffold-demo-ui-chat-app-shell`.
- Automated tests cover the new chat flow (sending a message, incremental rendering as stream chunks arrive, `thread_id` capture/reuse across two messages, and the error state) using a mocked `fetch` returning a `ReadableStream` body - no real network/backend calls. `npm run build`, `npm run lint`, and `npm test` all stay clean.
- Explicitly out of scope: RAG grounding, real tool-calling UI, persisting conversations across page reloads/sessions, and any change to `demo-api`.

## Rationale

- This closes the loop the campaign's acceptance shape describes ("a React application that talks to an LLM agent running behind a FastAPI endpoint") - the prior two encounters built each side of that connection independently (`scaffold-demo-ui-chat-app-shell`'s placeholder UI, `add-streaming-chat-endpoint`'s backend), and this encounter is the wiring between them the user is now asking for.
- Rendering the reply incrementally (not buffering the full stream before displaying) is the whole point of having built a streaming endpoint - a UI that just awaits the full response and dumps it at once would silently discard the backend's actual streaming behavior and give a misleading demo.
- Extending the existing dev-only Vite proxy (rather than introducing CORS on `demo-api`, or a new proxy mechanism) keeps this encounter single-region, consistent with both prior encounters' scoping decisions; production-time API reachability remains an explicitly deferred question (already flagged in `scaffold-demo-ui-chat-app-shell`'s Rationale).
- Session-only (non-persisted) `thread_id` state keeps this encounter's scope to "make multi-turn conversation work while the tab is open," matching the user's "getting all of the components wired up" framing rather than building out full conversation persistence/history UX.
- Mocking `fetch`'s streaming `Response.body` (rather than skipping streaming-specific tests) is necessary to actually verify incremental rendering, the feature's whole point - a test that only checks the final rendered text wouldn't catch a regression to non-streaming (buffered) rendering.

## Plan

1. In `packages/demo-ui/vite.config.ts`, add `/chat` alongside the existing `/health` proxy entry, forwarding to `http://localhost:8000`.
2. Add `src/api/chat.ts`: a `streamChat({thread_id, message}, onChunk)` function that `POST`s to `/chat`, reads `response.body` via a `ReadableStream` reader + `TextDecoder`, splits on newlines, `JSON.parse`s each line's `{"content": "..."}`, and invokes `onChunk` with each content delta; also returns the resolved `thread_id` read from the `X-Thread-Id` response header.
3. Add `src/hooks/useChat.ts`: manages the message list (`{role: 'user' | 'assistant', content: string}[]`), the current `thread_id` (component state, `undefined` until the first response), and a `sending` boolean; exposes a `sendMessage(text)` function that appends the user's message, calls `streamChat`, appends/updates a streaming assistant message as chunks arrive, captures/stores the returned `thread_id` for subsequent calls, and sets an error message on failure.
4. Update `src/components/ChatPlaceholder.tsx` (renamed to `Chat.tsx` if the placeholder-only name no longer fits, updating `App.tsx`'s import accordingly) to use `useChat`: render the message list (replacing "Chat coming soon." once there's at least one message), enable the input/send button, wire form submit to `sendMessage`, disable input while `sending`, and render any error state inline.
5. Add/update tests mocking `fetch` to return a `Response`-like object with a `ReadableStream` body (chunks split across multiple `read()` calls to genuinely exercise incremental parsing, not one single buffered chunk) - covering: sending a message renders both the user message and the incrementally-streamed assistant reply; the `thread_id` from the first response's `X-Thread-Id` header is sent on the second request; a failed `fetch` (rejected promise or non-2xx) surfaces an inline error and re-enables the input.
6. Run `npm run build`, `npm run lint`, `npm test` in `packages/demo-ui`.
7. Manual verification: run `demo-api` (with a real `.env`/`OPENROUTER_API_KEY`) and `demo-ui`'s dev server together, send a message in the browser, confirm the reply renders incrementally, send a second message, and confirm the model's reply reflects the first turn (multi-turn via the captured `thread_id`).

## Verification

- `npm run build`, `npm run lint`, `npm test` all pass in `packages/demo-ui`, with the new tests exercising genuine incremental-stream parsing (not just a single buffered mock chunk).
- `pdm run pytest -q` and `pdm run ruff check .` / `ruff format .` stay clean (unaffected, since no Python files change).
- Manual run as in Plan step 7, confirmed in a browser: incremental rendering visible, and multi-turn continuity works via the automatically-captured `thread_id`.

## Log

### Review - 2026-08-06T04:31:20Z - John Hoff

Reviewed against the single applicable lore item, `clean-tests-and-lint` (world-assigned): the Plan and Verification section honor it correctly, explicitly carrying forward the `pdm run pytest -q` / `ruff check`/`format` gate (correctly noted as unaffected since this encounter touches only `packages/demo-ui`) and adding an equivalent `npm run build`/`lint`/`test` gate for the JS side, with no skip/`--no-verify`/`noqa` shortcuts proposed. Cross-checked the Plan's file references against the actual repo state - `packages/demo-ui` is already scaffolded exactly as the Plan assumes (`vite.config.ts` has the single `/health` proxy entry to be extended, `ChatPlaceholder.tsx`, `src/api/health.ts`, and `src/hooks/useHealthStatus.ts` all exist as the patterns the new `chat.ts`/`useChat.ts` are meant to follow), so the Plan is well-grounded and feasible. One documentation note, not a Plan defect: the `demo-ui` region's body is stale, still describing the package as unscaffolded/nonexistent, which should probably be refreshed at some point but doesn't block this encounter. PASS-WITH-NOTES.

### Completed - 2026-08-06T04:46:34Z - John Hoff

All Requirements met and Verification passed: npm run build/lint/test all clean in packages/demo-ui (8/8 tests passing, including 3 new Chat tests exercising genuine cross-chunk stream parsing via a real multi-chunk ReadableStream mock, thread_id reuse across two requests, and the error path). pdm run pytest -q (771 passed) and ruff check/format stayed clean and unaffected, since no Python files changed. Manual dual-server run confirmed in a real browser: sending a message rendered the streamed assistant reply, a second message correctly reused the auto-captured thread_id and the model accurately quoted back the first turn's exact message, confirming multi-turn continuity through the UI end-to-end. Also refreshed the demo-ui region doc (was stale, still described the package as unscaffolded) per the reviewer's note. Confirmed complete with the GM.
