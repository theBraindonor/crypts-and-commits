---
archived: false
campaign: v0.1.7-rag-demo-application
created_by: John Hoff
created_on: '2026-08-05T16:43:13Z'
depends_on:
- bootstrap-fastapi-app-shell
name: scaffold-demo-ui-chat-app-shell
regions:
- demo-ui
status: completed
updated_by: John Hoff
updated_on: '2026-08-05T17:04:00Z'
---

## Requirements

- `packages/demo-ui` exists as a Node.js + React (TypeScript) application scaffolded with Vite, runnable via `npm install && npm run dev`.
- The app renders a header bar reading "Crypts and Commits Demo Chatbot" alongside a live backend-status indicator.
- The status indicator polls demo-api's `GET /health` on an interval and reflects `checking` / `online` / `offline` state without a page reload, transitioning correctly in both directions (backend up → down, down → up).
- A structural chat placeholder area exists below the header (empty message list + disabled input + disabled send button) as a hook point for future chatbot functionality — no chat logic implemented yet.
- No state-management library, CSS framework, or backend/production API-reachability code is introduced beyond a dev-only Vite proxy for the health check.
- `packages/demo-ui` is a Node package, not added to the root PDM workspace; nothing in root `pyproject.toml` changes.

## Rationale

- First concrete step of `demo-ui` within the `v0.1.7-rag-demo-application` campaign, establishing the Node/React tooling choice (Vite + TypeScript + npm) the `demo-ui` region's lore/summary flagged as unset.
- Mirrors `bootstrap-fastapi-app-shell`'s precedent: the narrowest runnable shell before any RAG/LLM UI work lands on top, deferring chat logic, state management, and styling-framework decisions to later encounters.
- The health-status indicator is pulled forward from the aspirational chatbot UI because the user explicitly asked for it now; it doubles as the cheapest possible end-to-end proof that `demo-ui` can reach `demo-api` before richer RAG wiring is attempted.
- A Vite dev-server proxy (not CORS) is used to reach `demo-api`'s `/health` endpoint, so this encounter touches only the `demo-ui` region and makes no change to `demo-api`. Production-time API reachability (proxy config, CORS, or same-origin deploy) is an explicit open question left for a later encounter once `demo-api` has a real deployment story.
- The world-assigned `clean-tests-and-lint` lore is stated in Python/pdm/ruff terms; since this encounter changes no Python files, that gate stays trivially satisfied. Equivalent JS-side gates (`npm run build`, `npm run lint`, `npm test`) are included in Verification as good practice for the new package, not because the lore literally mandates them.

## Plan

1. Scaffold with `npm create vite@latest demo-ui -- --template react-ts` run from `packages/`, producing `packages/demo-ui`.
2. In `vite.config.ts`, add a dev-server proxy forwarding `/health` to `http://localhost:8000` (demo-api's default `uvicorn` port) so the browser app can call same-origin `/health` in dev without CORS.
3. Add `src/api/health.ts`: a `fetchHealth()` wrapper calling `fetch('/health')` and returning a typed `{ success: boolean }` result (matching demo-api's actual response shape), resolving to a failure indicator on network error or non-2xx status.
4. Add `src/hooks/useHealthStatus.ts`: polls `fetchHealth()` once on mount and then on an interval (e.g. every 15s), exposing a `'checking' | 'online' | 'offline'` status value.
5. Add `src/components/Header.tsx`: an app header bar with the title "Crypts and Commits Demo Chatbot" and a status indicator (colored dot + text label) driven by `useHealthStatus`.
6. Add `src/components/ChatPlaceholder.tsx`: an empty message-list area plus a disabled input and disabled send button with a "Coming soon" note — structural only.
7. Wire `src/App.tsx` to render `Header` + `ChatPlaceholder`; strip the Vite template's default boilerplate (counter demo, logos, template `assets/`).
8. Add `vitest` + `@testing-library/react` (+ jsdom) as devDependencies, a `test` script in `package.json`, and a `vitest` config (reusing `vite.config.ts`'s `test` field or a sibling `vitest.config.ts`).
9. Add tests mocking `fetch`: `Header` renders the title; the status indicator shows `checking` before the first response, `online` on a successful `{success:true}` response, and `offline` on a failed/non-2xx response.
10. Confirm the Vite `react-ts` template's default ESLint config covers the new files cleanly (add/adjust a `lint` script if the template doesn't already provide one).

## Verification

- `npm run build` (type-check + production bundle) succeeds in `packages/demo-ui`.
- `npm run lint` passes with zero errors.
- `npm test` (Vitest) passes, covering the header title and all three status-indicator states.
- Manual run: start demo-api (`pdm run uvicorn demo_api.main:app --app-dir packages/demo-api/src`) and demo-ui (`npm run dev` in `packages/demo-ui`); confirm in a browser that the header shows the title and an "online" indicator, then stop demo-api and confirm the indicator transitions to "offline" within one poll interval.
- `pdm run pytest -q` and `pdm run ruff check .` / `ruff format .` stay clean (unaffected, since no Python files change).

## Log

### Review - 2026-08-05T16:45:25Z - John Hoff

Reviewed against the single applicable lore item, world-assigned `clean-tests-and-lint`: the Plan honors it correctly — Verification explicitly keeps `pdm run pytest -q` and `ruff check . / ruff format .` passing, and the Rationale correctly recognizes this gate is Python/pdm/ruff-scoped and trivially satisfied since no Python files change, adding JS-equivalent checks (`npm run build`, `npm run lint`, `npm test`) as good practice rather than claiming they substitute for the lore itself. No region-assigned lore applies (`demo-ui` has none). Two items are noted as unverified rather than blocking: the claim that the health-check response shape matches demo-api's actual `/health` contract wasn't checkable within this review's bounded surface, and the region's own caution to confirm unset tooling/implementation choices with the user before assuming them is asserted as already addressed in the Rationale but not independently verifiable here. Passing with those notes.

### Message - 2026-08-05T16:57:01Z - John Hoff

Implementation notes, no Requirements/scope deviation: (1) The current `npm create vite@latest -- --template react-ts` scaffold ships `oxlint` (not ESLint) as its default linter, with a `lint` script already wired in package.json — used as-is rather than swapping in ESLint, since it satisfies the Plan's actual intent (a working lint gate), just with a different tool than the Plan's wording assumed. (2) Dropped `@testing-library/jest-dom` from the Plan's devDependency list after finding the tests didn't need its matchers — plain `screen.getByText` assertions (which throw if the element isn't found) were sufficient, avoiding an extra dependency and TS type-augmentation complexity for no functional gain. (3) Manual dual-server verification: found demo-api already running on port 8000 from a prior session; used it directly, stopped it to confirm the indicator transitions to "Offline" (confirmed via DOM/computed-style, not the screenshot tool, which failed to visually capture that exact header corner across several attempts despite the DOM/computed-style being unambiguous - documenting as a likely browser-extension screenshot artifact investigated and ruled out as an app bug), then restarted it and confirmed the indicator returns to "Online", completing both directions of the transition. Verification otherwise ran exactly as planned: `npm run build` (tsc -b + vite build) succeeded, `npm run lint` (oxlint) passed clean, and `npm test` (vitest) passed all 5 tests covering the title and checking/online/offline states.

### Completed - 2026-08-05T17:04:00Z - John Hoff

All Requirements met and Verification passed: npm run build (tsc -b + vite build), npm run lint (oxlint), and npm test (vitest, 5/5 passing) all clean; pdm run pytest -q / ruff stayed unaffected since no Python files changed. Manual dual-server check confirmed both directions of the health-status transition (online -> offline -> online) reflected live in the browser without a reload. As a small follow-on requested by the GM after this encounter's own Verification passed, the root README.md was also updated with run instructions for both demo-api and demo-ui and to drop demo-ui's "not yet added" note - done directly, without a separate encounter, per GM's explicit choice. Confirmed complete with the GM.
