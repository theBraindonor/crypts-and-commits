---
archived: false
campaign: v0.1.7-rag-demo-application
created_by: John Hoff
created_on: '2026-08-05T16:10:27Z'
depends_on: []
name: bootstrap-fastapi-app-shell
regions:
- demo-api
status: completed
updated_by: John Hoff
updated_on: '2026-08-05T16:33:08Z'
---

## Requirements

- `packages/demo-api` has real, importable app code (no more empty scaffold).
- Running the app exposes: a working Swagger UI at `/docs`, a `GET /health` endpoint returning a 200 JSON status response, and a `GET /` index page whose content links to `/docs`.
- `fastapi` and `uvicorn[standard]` are declared as direct dependencies of `packages/demo-api` and locked in `pdm.lock`.
- Automated tests cover all three endpoints and pass under `pdm run pytest -q`.
- `pdm run ruff check .` / `ruff format .` stay clean across the new code.

## Rationale

- `v0.1.7-rag-demo-application` needs a real running application before any RAG/retrieval work can land on top of it; this is the smallest slice that proves the package boots, serves HTTP, and is testable — establishing the shell every later encounter in this campaign extends.
- Swagger UI (free from FastAPI) and a simple health check are the standard first checkpoints for any new HTTP service — they're the fastest way to confirm the app is alive and self-documenting before adding real functionality.
- Scope is deliberately narrow: no RAG, no LLM/agent wiring, no `demo-ui` work, no new region lore. The `demo-api` region's summary already describes the larger aspirational RAG scope — this encounter is the first step toward it, not the whole thing.

## Plan

1. Add `fastapi` and `uvicorn[standard]` to `packages/demo-api`'s dependencies via `pdm add -p packages/demo-api fastapi "uvicorn[standard]"` (run from the repo root), updating both `packages/demo-api/pyproject.toml` and the root `pdm.lock` together.
2. Create `packages/demo-api/src/demo_api/__init__.py` (empty) and `packages/demo-api/src/demo_api/main.py` — mirroring `packages/crypts-and-commits`'s `src/` layout convention — containing:
   - `app = FastAPI(title=..., description=...)` (Swagger UI ships free at `/docs`, ReDoc at `/redoc` — no extra setup needed).
   - `GET /health` → returns a small JSON body (e.g. `{"status": "ok"}`).
   - `GET /` → returns an `HTMLResponse` with a minimal index page containing a link to `/docs`. Plain inline HTML string — no templating engine needed for one static page.
3. Create `packages/demo-api/tests/__init__.py` and `packages/demo-api/tests/test_main.py` — mirroring `packages/crypts-and-commits/tests/`'s subpackage-with-`__init__.py` convention, no shared `conftest.py` — using `fastapi.testclient.TestClient` (the direct analog of the existing `typer.testing.CliRunner` pattern):
   - `GET /health` → 200, expected JSON body.
   - `GET /` → 200, response contains a link to `/docs`.
   - `GET /docs` → 200 (Swagger UI actually reachable).
4. Run `pdm install` to pick up the new deps and refresh the editable install for `demo_api`.
5. Run the app locally (e.g. `pdm run uvicorn demo_api.main:app --reload --app-dir packages/demo-api/src`, or the equivalent once the editable install resolves `demo_api` directly) and manually confirm in a browser that `/` renders with a working link to `/docs`, that `/docs` shows the Swagger UI, and that `/health` returns the expected JSON.

## Verification

- `pdm run pytest -q` passes, including the new `demo-api` tests.
- `pdm run ruff check .` reports zero errors; `pdm run ruff format .` reports no diffs.
- Manual local run: start the server, confirm `/` renders with a working link to `/docs`, confirm `/docs` shows the Swagger UI, confirm `/health` returns the expected JSON.

## Log

### Review - 2026-08-05T16:12:34Z - John Hoff

Reviewed against the one applicable lore item, clean-tests-and-lint (world-assigned; demo-api carries no additional region lore). The Plan's Verification section explicitly commits to `pdm run pytest -q` passing and `ruff check`/`ruff format` being clean before completion, matching the lore's gate exactly — no skips, no deleted tests, no lint suppressions implied anywhere in the Plan. Scope is appropriately narrow (FastAPI shell only, no RAG/LangChain/LLM wiring), consistent with the encounter's own Rationale and the campaign's broader aspirational scope for demo-api, which this encounter correctly treats as not-yet-settled rather than building against prematurely. No lore conflicts found; approved to proceed to reviewed.

### Message - 2026-08-05T16:33:00Z - John Hoff

Implementation notes, no Plan deviation in substance: (1) Root pyproject.toml's [tool.pytest.ini_options] gained `addopts = "--import-mode=importlib"` — required because packages/demo-api/tests and packages/crypts-and-commits/tests both use a top-level `tests` package with __init__.py, and pytest's default prepend import mode collided the two under the same module name, making demo-api's tests uncollectable. importlib mode is the standard fix for this monorepo pattern and does not affect existing tests. (2) On this Windows dev environment, `pdm install`/`pdm sync --reinstall` could not fully resync because this session's own crypts-and-commits MCP server process holds an OS-level lock on .venv/Scripts/cac-mcp.exe (and, under a full reinstall, other in-use venv files). Rather than force a broad reinstall, hand-wrote .venv/Lib/site-packages/demo_api.pth pointing at packages/demo-api/src, the same mechanism PDM's own editable install uses (matching the existing crypts_and_commits.pth) — demo-api's dependencies and pdm.lock were updated normally via `pdm add`, only the local venv sync step needed this workaround. (3) Per GM feedback after initial Verification, changed GET /health's response body from {"status": "ok"} to {"success": true} (and its test) — a same-scope refinement of an example body the Plan itself only specified as illustrative ("e.g."), not a Requirements change. Re-ran full Verification after the change: pdm run pytest -q (767 passed), ruff check/format clean, and a fresh manual server run confirming /health returns {"success":true} and / independently returns the HTML index with a working /docs link — the GM's initial observation of mixed content was a stale browser/test artifact from the first manual run, not a real routing defect.

### Completed - 2026-08-05T16:33:08Z - John Hoff

All Requirements met and Verification passed: pdm run pytest -q (767 passed), ruff check/format clean, and a fresh manual server run confirming / (HTML index linking to /docs), /docs (Swagger UI), and /health ({"success":true}) all work correctly and independently. Confirmed complete with the GM.
