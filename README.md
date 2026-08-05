# crypts-and-commits

A Coding Assistant Continuity Framework. Crypts and Commits uses a tabletop-gaming metaphor to describe collaboration between a developer and an AI coding assistant. The developer acts as the Game Master: establishing context, making decisions, and retaining final authority.

This repository is the development workspace for the project. It is a [PDM workspace](https://pdm-project.org/en/latest/usage/monorepo/) containing the individual packages that make up Crypts and Commits.

Adopting CAC in your own project? See the [Quickstart](docs/QUICKSTART.md).

## Packages

- [`packages/crypts-and-commits`](packages/crypts-and-commits) — the core framework.
- [`packages/demo-api`](packages/demo-api) — a demonstration API used for development testing within the project.
- [`packages/demo-ui`](packages/demo-ui) — a demonstration UI (Node.js/React) that exercises the demo API.

## Running the demo apps

`demo-api` and `demo-ui` are two independent servers, run in separate terminals.

### demo-api

From the repository root:

```
pdm install
pdm run uvicorn demo_api.main:app --app-dir packages/demo-api/src --reload
```

Serves on http://localhost:8000 — Swagger UI at `/docs`, health check at `/health`.

### demo-ui

```
cd packages/demo-ui
npm install
npm run dev
```

Serves on http://localhost:5173. In dev mode, requests to `/health` are proxied to `demo-api` on port 8000 (see `packages/demo-ui/vite.config.ts`), so start `demo-api` first to see the header's status indicator go online.
