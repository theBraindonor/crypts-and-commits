# demo-ui

The chat frontend for [`demo-api`](../demo-api/README.md), demonstrating
[Crypts and Commits](../../README.md) (CAC) end to end: a browser-based Q&A
client for an agent that answers questions about this repository, grounded
in its own live `.sourcebook` content, independent of any coding-assistant
harness.

## How it works

- **Vite + React + TypeScript**, plain React state/hooks — no state-management
  library or CSS framework.
- A header bar shows a live backend-health indicator, polling `demo-api`'s
  `/health` endpoint every 15 seconds.
- The chat panel streams `demo-api`'s `POST /chat` response token-by-token
  into the assistant's message as it arrives, renders assistant replies as
  markdown (`react-markdown` + `remark-gfm`), and carries the conversation's
  `thread_id` across turns so multi-turn context is preserved; "New chat"
  resets it.
- In dev mode, `/health` and `/chat` requests are proxied to `demo-api` on
  `localhost:8000` (see `vite.config.ts`) rather than using CORS, so start
  `demo-api` first.

## Running it

```bash
cd packages/demo-ui
npm install
npm run dev
```

Serves on http://localhost:5173. Start [`demo-api`](../demo-api/README.md)
first (`localhost:8000`) so the header's status indicator goes online and
the chat panel has something to talk to.

## Other scripts

```bash
npm run build     # type-check (tsc -b) and produce a production build
npm run preview   # serve the production build locally
npm run test      # run the Vitest + React Testing Library suite
npm run lint      # oxlint
```

## Learn more

- [Root repository README](../../README.md) — what Crypts and Commits is and
  how this package fits into the workspace.
- [`demo-api`](../demo-api/README.md) — the backend this UI talks to.
