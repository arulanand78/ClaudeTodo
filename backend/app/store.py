"""Persistence layer for todos.

A storage interface is defined so the in-memory implementation can be
swapped for a database later without changing the routes (PRD §8).
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol
from uuid import UUID, uuid4

from .models import Todo, TodoCreate, TodoUpdate


class TodoStore(Protocol):
    """Storage interface for todos."""

    def list_all(self) -> list[Todo]: ...
    def create(self, payload: TodoCreate) -> Todo: ...
    def update(self, todo_id: UUID, payload: TodoUpdate) -> Todo | None: ...
    def delete(self, todo_id: UUID) -> None: ...


class InMemoryTodoStore:
    """Single-process in-memory store (PRD §8).

    Not thread-safe by itself; relies on Uvicorn's single event loop.
    Useful for throwaway runs via ``TODO_STORE=memory``.
    """

    def __init__(self) -> None:
        self._items: dict[UUID, Todo] = {}
        self._order: dict[UUID, int] = {}  # monotonic tiebreaker per todo

    def list_all(self) -> list[Todo]:
        # Newest first by created_at (PRD §5.2). The sequence breaks ties when
        # the system clock's resolution makes two timestamps equal (e.g. on
        # Windows), preserving correct insertion order.
        return sorted(
            self._items.values(),
            key=lambda t: (t.created_at, self._order[t.id]),
            reverse=True,
        )

    def create(self, payload: TodoCreate) -> Todo:
        todo = Todo(
            id=uuid4(),
            title=payload.title,
            completed=False,
            created_at=datetime.now(timezone.utc),
        )
        self._order[todo.id] = len(self._order)  # monotonic creation index
        self._items[todo.id] = todo
        return todo

    def update(self, todo_id: UUID, payload: TodoUpdate) -> Todo | None:
        todo = self._items.get(todo_id)
        if todo is None:
            return None
        updated = todo.model_copy(update={"completed": payload.completed})
        self._items[todo_id] = updated
        return updated

    def delete(self, todo_id: UUID) -> None:
        # Idempotent: deleting a missing id is a no-op (PRD §5.2).
        self._items.pop(todo_id, None)
        self._order.pop(todo_id, None)


class SqliteTodoStore:
    """Persistent store backed by a SQLite file.

    Survives process restarts. The DB path defaults to ``backend/todos.db``
    and can be overridden with the ``TODO_DB_PATH`` env var.

    A fresh connection is opened per operation: FastAPI runs sync route
    handlers in a threadpool, so concurrent requests may land on different
    threads, and sqlite3 connections are thread-local by default. Per-call
    connections sidestep cross-thread issues without a global lock.
    """

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        # Ensure the parent directory exists (e.g. when TODO_DB_PATH points
        # somewhere that hasn't been created yet).
        db_path.parent.mkdir(parents=True, exist_ok=True)
        # Create the schema up front so the first request doesn't pay for it.
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS todos (
                    id          TEXT PRIMARY KEY,
                    title       TEXT NOT NULL,
                    completed   INTEGER NOT NULL DEFAULT 0,
                    created_at  TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        # WAL gives better concurrency for the rare overlapping read/write.
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    @staticmethod
    def _row_to_todo(row: sqlite3.Row) -> Todo:
        return Todo(
            id=UUID(row["id"]),
            title=row["title"],
            completed=bool(row["completed"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def list_all(self) -> list[Todo]:
        # Newest first by created_at (PRD §5.2). SQLite's hidden rowid is a
        # monotonic insertion counter, so it breaks ties when the system
        # clock's resolution makes two timestamps equal (e.g. on Windows) —
        # mirroring the in-memory store's creation_index tiebreaker.
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, title, completed, created_at, rowid "
                "FROM todos ORDER BY created_at DESC, rowid DESC"
            ).fetchall()
        return [self._row_to_todo(r) for r in rows]

    def create(self, payload: TodoCreate) -> Todo:
        todo = Todo(
            id=uuid4(),
            title=payload.title,
            completed=False,
            created_at=datetime.now(timezone.utc),
        )
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO todos (id, title, completed, created_at) "
                "VALUES (?, ?, 0, ?)",
                (str(todo.id), todo.title, todo.created_at.isoformat()),
            )
            conn.commit()
        return todo

    def update(self, todo_id: UUID, payload: TodoUpdate) -> Todo | None:
        with self._connect() as conn:
            cur = conn.execute(
                "UPDATE todos SET completed = ? WHERE id = ?",
                (1 if payload.completed else 0, str(todo_id)),
            )
            if cur.rowcount == 0:
                return None  # route raises 404
            row = conn.execute(
                "SELECT id, title, completed, created_at FROM todos WHERE id = ?",
                (str(todo_id),),
            ).fetchone()
            conn.commit()
        return self._row_to_todo(row)

    def delete(self, todo_id: UUID) -> None:
        # Idempotent: deleting a missing id is a no-op (PRD §5.2).
        with self._connect() as conn:
            conn.execute("DELETE FROM todos WHERE id = ?", (str(todo_id),))
            conn.commit()


# Select the store implementation. The persistent SQLite store is the
# default; TODO_STORE=memory switches back to the throwaway in-memory store.
def _default_db_path() -> Path:
    # backend/app/store.py -> backend/todos.db
    return Path(__file__).resolve().parent.parent / "todos.db"


if os.environ.get("TODO_STORE", "").lower() == "memory":
    store: TodoStore = InMemoryTodoStore()
else:
    store: TodoStore = SqliteTodoStore(
        Path(os.environ.get("TODO_DB_PATH", str(_default_db_path())))
    )