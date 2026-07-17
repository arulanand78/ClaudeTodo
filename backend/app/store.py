"""Persistence layer for todos.

A storage interface is defined so the in-memory implementation can be
swapped for a database later without changing the routes (PRD §8).
"""

from __future__ import annotations

from datetime import datetime, timezone
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
    """Single-process in-memory store for v1 (PRD §8).

    Not thread-safe by itself; relies on Uvicorn's single event loop.
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


# Single shared instance for v1.
store: TodoStore = InMemoryTodoStore()