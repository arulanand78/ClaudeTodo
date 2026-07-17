"""Todo routes (PRD §6)."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from ..models import Todo, TodoCreate, TodoUpdate
from ..store import store

router = APIRouter(prefix="/todos", tags=["todos"])


@router.post("", response_model=Todo, status_code=status.HTTP_201_CREATED)
def create_todo(payload: TodoCreate) -> Todo:
    return store.create(payload)


@router.get("", response_model=list[Todo], status_code=status.HTTP_200_OK)
def list_todos() -> list[Todo]:
    return store.list_all()


@router.patch("/{todo_id}", response_model=Todo, status_code=status.HTTP_200_OK)
def update_todo(todo_id: UUID, payload: TodoUpdate) -> Todo:
    updated = store.update(todo_id, payload)
    if updated is None:
        raise HTTPException(status_code=404, detail="todo not found")
    return updated


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: UUID) -> None:
    store.delete(todo_id)