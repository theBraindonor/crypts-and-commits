---
name: demo-ui
path: packages/demo-ui
summary: 'Frontend region packages/demo-ui: Vite+React 19+TS (npm, outside the PDM
  workspace) chat client for demo-api. Streams POST /chat NDJSON via a dev-only Vite
  proxy, keeps the X-Thread-Id thread in memory, renders replies as GFM markdown (react-markdown),
  header with health indicator, New Chat and GitHub link. Plain React state and CSS;
  Vitest+RTL, oxlint. Conversation persistence across reloads and the production build/deploy
  story are unconfirmed.'
updated_by: John Hoff
updated_on: '2026-11-23T18:44:13Z'
---

# Demo UI (frontend)

The chat frontend for demo-api, demonstrating crypts-and-commits end to end: a developer chats with an assistant grounded in this project's sourcebook.

## Current state

- Vite + React 19 + TypeScript app (npm; not part of the PDM workspace, which covers only Python packages).
- Chat wired to demo-api's streaming `POST /chat` (`src/api/chat.ts`, `src/hooks/useChat.ts`, `src/components/Chat.tsx`): reads the NDJSON stream line by line, appends `content` chunks to the assistant reply, and carries the `X-Thread-Id` response header forward as `thread_id` on later messages.
- Assistant replies render as GitHub-flavored markdown (`react-markdown` + `remark-gfm`).
- Header: title, live backend-health indicator (polls `/health`), a New Chat button that resets messages and thread, and a GitHub source link. Banner-derived theme in plain CSS.
- Tests: Vitest + React Testing Library (jsdom). Lint: the Vite template's `oxlint`. Scripts: `npm run dev|build|lint|test`.

## Confirmed technology decisions

- Vite bundler/dev server, npm package manager.
- No state-management library or CSS framework: plain React state/hooks and plain CSS.
- Dev-time API access via the Vite dev-server proxy (`/health`, `/chat` → `http://localhost:8000`), not CORS, so demo-ui stays self-contained without demo-api changes.
- Sourcebook grounding lives in demo-api (live prime bundle + read-only `cac.core` tools); demo-ui is a thin client and does no retrieval itself.

## Still to confirm

- Conversation persistence across page reloads (the thread id and messages are in-memory React state only; demo-api's SQLite checkpointer persists server-side).
- Production build/deploy story and how it reaches a deployed demo-api (proxy vs. CORS vs. same-origin).

Treat anything under "Still to confirm" as unsettled; confirm with the developer before assuming details not reflected in code.
