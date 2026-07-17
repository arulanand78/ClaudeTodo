"""Pydantic schemas for the Todo API (PRD §5.1, §6)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class TodoCreate(BaseModel):
    """Request body for creating a todo."""

    title: str = Field(..., max_length=255)

    @field_validator("title")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("title must not be empty or whitespace-only")
        return trimmed


class TodoUpdate(BaseModel):
    """Request body for toggling completion."""

    completed: bool


class Todo(BaseModel):
    """Todo response model."""

    id: UUID
    title: str
    completed: bool
    created_at: datetime