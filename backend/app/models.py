"""Pydantic schemas for the Todo API (PRD §5.1, §6)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

# The fixed set of categories a todo may belong to. The first entry is the
# default used when a create request omits `category` and the value backfilled
# onto pre-category rows during the SQLite migration. The wire/storage value is
# the human-readable label (e.g. "General"), kept in sync with the frontend's
# CATEGORIES constant.
CATEGORIES: tuple[str, ...] = ("General", "Work", "Personal", "Shopping", "Health")
DEFAULT_CATEGORY = CATEGORIES[0]


class TodoCreate(BaseModel):
    """Request body for creating a todo."""

    title: str = Field(..., max_length=255)
    category: str = Field(default=DEFAULT_CATEGORY)

    @field_validator("title")
    @classmethod
    def _non_empty_title(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("title must not be empty or whitespace-only")
        return trimmed

    @field_validator("category")
    @classmethod
    def _valid_category(cls, value: str) -> str:
        trimmed = value.strip()
        if trimmed not in CATEGORIES:
            raise ValueError(
                "category must be one of: " + ", ".join(CATEGORIES)
            )
        return trimmed


class TodoUpdate(BaseModel):
    """Request body for toggling completion.

    Category is immutable after creation, so only `completed` is accepted
    here (PRD §5.2).
    """

    completed: bool


class Todo(BaseModel):
    """Todo response model."""

    id: UUID
    title: str
    completed: bool
    category: str
    created_at: datetime