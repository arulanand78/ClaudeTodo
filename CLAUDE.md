# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

ClaudeTodo is a two-part app: a React (Vite) SPA frontend and a Python (FastAPI) backend, coupled by a REST API at `/api`. There are **no user accounts** — todos persist to a local SQLite file (`backend/todos.db`, via stdlib `sqlite3`) that survives process restarts. `PRD.md` is the source of truth for intended behavior; the README is partially stale (it predates the `app/` package restructure).

## Commands

Backend (run from `backend/`):
```bash
python -m venv .venv && source .venv/Scripts/activate   # Windows Git Bash; see README for other shells
pip install -r requirements.txt
uvicorn app.main:app --reload                            # serves :8000, OpenAPI at /docs
```

Frontend (run from `frontend/`):
```bash
npm install
npm run dev      # :5173, proxies /api -> :8000
npm run build    # production build to dist/
```

There is **no test suite**. To exercise the API end-to-end, run an inline TestClient script from `backend/` (requires `pip install httpx`):
```bash
python -c "from fastapi.testclient import TestClient; from app.main import app; c=TestClient(app); print(c.post('/api/todos', json={'title':'x'}).json())"
```

Run both halves together for the dev experience: backend on `:8000`, frontend on `:5173` (Vite proxies `/api`, so the SPA uses relative URLs only — never hardcode `localhost:8000` in client code).

## Architecture

**Backend (`backend/app/`, FastAPI)** is layered so the persistence layer can be swapped without touching routes:
- `models.py` — Pydantic v2 schemas. `TodoCreate` enforces title `max_length=255` and rejects empty/whitespace via a `field_validator` that **trims** before validating. It also carries an optional `category` (default `General`) validated against the fixed set `CATEGORIES` in the same file. `TodoUpdate` only accepts `completed` — category is immutable after creation.
- `store.py` — `TodoStore` `Protocol` (the seam) + two impls: `SqliteTodoStore` (the default; persists to a local SQLite file) and `InMemoryTodoStore` (throwaway). A module-level `store` singleton is injected by the routes. Swapping impls means writing a new class that satisfies the protocol; routes stay untouched. Selection is env-driven: `TODO_STORE=memory` for the in-memory store; `TODO_DB_PATH` relocates the SQLite file (default `backend/todos.db`).
- `routers/todos.py` — the four REST routes, mounted under `/api` in `main.py`.
- `main.py` — app, CORS (`http://localhost:5173` only), router mount, `/health`, and a `RequestValidationError` handler.

Two non-obvious backend behaviors, both intentional:
1. **Validation errors return `400`, not `422`.** FastAPI/Pydantic default to `422` with an array body. The custom `RequestValidationError` handler in `main.py` converts these to `400` with `{ "detail": "..." }` (a string) to match the PRD's error contract. If you add new request models, they inherit this automatically.
2. **Newest-first ordering uses a monotonic sequence tiebreaker.** `list_all` sorts by `(created_at, creation_index)` descending — in `InMemoryTodoStore` this is an explicit per-todo counter; in `SqliteTodoStore` it's SQLite's auto-incrementing `rowid` (`ORDER BY created_at DESC, rowid DESC`). Windows' system-clock resolution (~15ms) makes back-to-back creates share a `created_at` timestamp, which would scramble insertion order without the tiebreaker.

**Frontend (`frontend/src/`, React 19 + Vite)** — no state library; `App.jsx` holds all state in hooks:
- `api.js` — fetch client. Uses **relative** `/api/...` URLs (the Vite proxy handles dev; relative URLs also work for preview builds). Parses `{detail}` errors into messages. Exports the fixed `CATEGORIES` list and `FILTER_ALL` sentinel.
- `App.jsx` — single page: input + category `<select>` + Add, a category filter `<select>`, and a list of todos (checkbox + delete). All mutations are **optimistic** (local state updated immediately), then **reconcile on success**, or **rollback + refetch on error**. It also does a `GET` on mount so a reload reflects server state. Category filtering is **client-side** over the already-loaded list; the header counts are computed from the full list, not the filtered view.
- `vite.config.js` — the `/api` → `http://localhost:8000` proxy; this is why client code must use relative URLs.

## API contract (the seam between the two halves)

All under `/api`, JSON in/out. Keep this in sync when changing either side.

| Method | Path | Body | Success | Failure |
|---|---|---|---|---|
| POST | `/todos` | `{ "title": "...", "category": "..." }` (`category` optional, default `General`) | `201` `{ id, title, completed, category, created_at }` | `400` bad title / unknown category |
| GET | `/todos` | — | `200` `[ ... ]` (newest first) | — |
| PATCH | `/todos/{id}` | `{ "completed": bool }` | `200` `{ ... }` | `404` unknown id |
| DELETE | `/todos/{id}` | — | `204` (idempotent: missing id also `204`) | — |

`id` is a UUID; `created_at` is an ISO-8601 UTC timestamp set by the server. `category` is one of a fixed set (`General`, `Work`, `Personal`, `Shopping`, `Health`); it is set at creation (defaulting to `General`), **immutable** afterward, and validated against the set (unknown value → `400`). Category **filtering is client-side** — `GET /api/todos` always returns all todos; the UI filters the already-loaded list. Error shape is always `{ "detail": "..." }`.