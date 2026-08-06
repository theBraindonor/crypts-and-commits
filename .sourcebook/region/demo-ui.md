---
name: demo-ui
path: packages/demo-ui
summary: 'Frontend region packages/demo-ui. Scaffolded: Vite+React+TS (npm), header
  with health indicator via dev-only Vite proxy, Vitest+RTL, oxlint. Chat UI wiring
  to demo-api''s streaming POST /chat is next (in progress). No state-mgmt lib/CSS
  framework. RAG grounding, conversation persistence, and production deploy/reachability
  remain unconfirmed.'
updated_by: John Hoff
updated_on: '2026-08-06T04:31:34Z'
---

# Demo UI (frontend)

The chat frontend for the demo-api RAG chatbot, demonstrating crypts-and-commits end to end.

## Current state

- Scaffolded (`scaffold-demo-ui-chat-app-shell` encounter): a Vite + React + TypeScript app (npm, not part of the PDM workspace, which only covers Python packages). Header bar with title and a live backend-health indicator (polls `demo-api`'s `/health` via a dev-only Vite proxy). Vitest + React Testing Library for tests; the Vite `react-ts` template's bundled `oxlint` for linting.
- A functional chat UI wired to `demo-api`'s streaming `POST /chat` is the next concrete step (`wire-demo-ui-chat-endpoint` encounter) - replacing the current disabled placeholder input/message-list with a real, streaming conversation.

## Confirmed technology decisions

- **Vite** as the bundler/dev server, **npm** as the package manager - both were open questions until `scaffold-demo-ui-chat-app-shell` settled them.
- No state-management library or CSS framework introduced - plain React state/hooks and plain CSS.
- Talks to `demo-api` in dev via a Vite dev-server proxy (`vite.config.ts`), not CORS - keeps `demo-ui` changes self-contained without requiring `demo-api` changes. Production-time API reachability (proxy vs. CORS vs. same-origin deploy) is still an open question.

## Still to confirm

- RAG grounding in `.sourcebook` content - the chat UI/backend wiring so far is plumbing only, no retrieval yet.
- Conversation persistence across page reloads/sessions (current/planned `thread_id` handling is session-only, in-memory React state).
- Production build/deploy story for `demo-ui` and how it reaches a deployed `demo-api`.

## Status

Scaffolded and being wired to the backend. Treat anything under "Still to confirm" as unsettled - confirm with the user before assuming implementation details not yet reflected in code.
