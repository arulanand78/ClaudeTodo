# CLAUDE.md — backend

FastAPI backend for ClaudeTodo. The shared API contract, project overview, and dev orchestration live in the **root `../CLAUDE.md`** — read that first; this file covers backend-only specifics.

## Run

```bash
python -m venv .venv && source .venv/Scripts/activate   # Windows Git Bash
pip install -r requirements.txt
uvicorn app.main:app --reload        # :8000, OpenAPI at /docs
```

For end-to-end API checks there is **no test suite** — run an inline TestClient script (needs `pip install httpx`):
```bash
python -c "from fastapi.testclient import TestClient; from app.main import app; c=TestClient(app); print(c.get('/api/todos').json())"
```

## Layout (`app/` package — imported as `app.main`, hence `uvicorn app.main:app`)

- `app/main.py` — FastAPI app, CORS (origin `http://localhost:5173` only), mounts `routers.todos` under `/api`, `/health`, and the validation→400 handler.
- `app/models.py` — Pydantic v2 schemas. `TodoCreate.title` has `max_length=255` and a `field_validator` that **trims then rejects empty/whitespace**. `TodoCreate.category` is optional (default `General`) and validated against the fixed `CATEGORIES` tuple in this file (unknown value → 400). `TodoUpdate` only accepts `completed` — category is immutable after creation.
- `app/store.py` — `TodoStore` `Protocol` (the seam) + two impls (`SqliteTodoStore` default, `InMemoryTodoStore` throwaway) + a module-level `store` singleton the routes import. Selection is env-driven: `TODO_STORE=memory` uses the in-memory store; `TODO_DB_PATH` relocates the SQLite file (default `backend/todos.db`). `sqlite3` is stdlib — no dependency added.
- `app/routers/todos.py` — the four REST routes (see root `CLAUDE.md` for the contract).

## Conventions that aren't obvious from the code

- **Store is the seam.** Routes depend on the `store` singleton and the `TodoStore` protocol, never on a concrete store class directly. The default is `SqliteTodoStore` (persists to SQLite); `InMemoryTodoStore` is selected via `TODO_STORE=memory`. Adding a new backend = write a new class that satisfies the protocol and reassign `store`; do not touch `routers/`. Do not reach into store internals from routes.
- **Bad input → `400`, not `422`.** FastAPI/Pydantic default to `422` with an array body. The `RequestValidationError` handler in `main.py` flattens that to `400` with `{ "detail": "..." }` (string) per the PRD. New request models inherit this automatically — do not add per-route `try/except` for validation.
- **Unknown id on PATCH → `404`** (raise `HTTPException(404)`); **unknown id on DELETE → `204`** (idempotent, no-op). Keep this asymmetry.
- **Newest-first ordering uses a monotonic tiebreaker.** `list_all` sorts newest-first with a monotonic tiebreaker because Windows clock resolution (~15ms) can make consecutive creates share a timestamp. In `InMemoryTodoStore` this is an explicit per-todo `creation_index`; in `SqliteTodoStore` it's the auto-incrementing `rowid` (`ORDER BY created_at DESC, rowid DESC`). If you change ordering or stores, preserve a deterministic tiebreaker.
- **`category` is a migrated column.** Pre-category `todos.db` files lack the `category` column; `SqliteTodoStore.__init__` adds it via an idempotent `ALTER TABLE … ADD COLUMN category TEXT NOT NULL DEFAULT 'General'` (guarded by a `PRAGMA table_info` check), backfilling existing rows with `General`. `CREATE TABLE IF NOT EXISTS` alone won't add a column to an existing table, hence the explicit alter. When adding further nullable-with-default columns later, follow the same pattern.
- Timestamps are `datetime.now(timezone.utc)` — timezone-aware, serialized as ISO-8601 UTC. Don't switch to naive datetimes.