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
- `app/models.py` — Pydantic v2 schemas. `TodoCreate.title` has `max_length=255` and a `field_validator` that **trims then rejects empty/whitespace**.
- `app/store.py` — `TodoStore` `Protocol` (the seam) + `InMemoryTodoStore` (the impl) + a module-level `store` singleton the routes import.
- `app/routers/todos.py` — the four REST routes (see root `CLAUDE.md` for the contract).

## Conventions that aren't obvious from the code

- **Store is the seam.** Routes depend on the `store` singleton and the `TodoStore` protocol, never on `InMemoryTodoStore` directly. Adding persistence = write a new class that satisfies the protocol and reassign `store`; do not touch `routers/`. Do not reach into `InMemoryTodoStore` internals from routes.
- **Bad input → `400`, not `422`.** FastAPI/Pydantic default to `422` with an array body. The `RequestValidationError` handler in `main.py` flattens that to `400` with `{ "detail": "..." }` (string) per the PRD. New request models inherit this automatically — do not add per-route `try/except` for validation.
- **Unknown id on PATCH → `404`** (raise `HTTPException(404)`); **unknown id on DELETE → `204`** (idempotent, no-op). Keep this asymmetry.
- **Newest-first ordering uses a monotonic tiebreaker.** `list_all` sorts by `(created_at, creation_index)` descending because Windows clock resolution (~15ms) can make consecutive creates share a timestamp. If you change ordering, preserve a deterministic tiebreaker.
- Timestamps are `datetime.now(timezone.utc)` — timezone-aware, serialized as ISO-8601 UTC. Don't switch to naive datetimes.