# Product Requirements Document — ClaudeTodo

**Version:** 1.0
**Date:** 2026-07-13
**Status:** Draft

## 1. Overview

ClaudeTodo is a lightweight task-management application that lets users capture, complete, and remove to-do items. The goal is a fast, minimal, no-friction todo list — fast load, no clutter, reliable sync between client and server. It serves as a reference stack pairing a React (Vite) frontend with a Python FastAPI backend.

## 2. Goals & Non-Goals

**Goals**
- Let a user create, complete, and delete todos with zero configuration.
- Provide a clean, responsive single-page UI backed by a REST API.
- Keep the stack simple and maintainable: React + Vite on the client, FastAPI on the server, a single persistence store.

**Non-Goals (v1)**
- User accounts, authentication, or multi-tenant isolation.
- Due dates, tags, priorities, sub-tasks, or nested lists.
- Offline mode, real-time collaboration, or sync across devices.
- Notifications or reminders.

## 3. Users & Personas

A single anonymous user interacting with their own local todo list. No login, no shared state. All data is global to the running instance in v1.

## 4. User Stories

- As a user, I can add a new todo by typing text and submitting, so I don't forget things.
- As a user, I can see all my todos in a single list, so I know what's outstanding.
- As a user, I can mark a todo as complete, so I can track progress.
- As a user, I can unmark a completed todo, so I can correct mistakes.
- As a user, I can delete a todo, so I can remove items I no longer need.
- As a user, I can tell completed and active todos apart at a glance.

## 5. Functional Requirements

### 5.1 Todo Model
Each todo has:
- `id` — unique identifier (UUID).
- `title` — non-empty string, max 255 chars, trimmed.
- `completed` — boolean, defaults to `false`.
- `created_at` — ISO-8601 timestamp, server-set.

### 5.2 Core Actions
- **Create** — Add a todo from a title. Reject empty/whitespace-only titles.
- **Read** — List all todos. Ordering: newest first by `created_at`.
- **Update** — Toggle `completed` on a todo by id.
- **Delete** — Remove a todo by id. Idempotent: deleting a missing id returns success (204).

### 5.3 Validation & Errors
- Title > 255 chars → `400` with a clear message.
- Unknown id on toggle → `404`.
- Server returns JSON errors of the form `{ "detail": "..." }`.

## 6. API Design

Base URL: `/api`. JSON in/out.

| Method | Path | Body | Success | Purpose |
|---|---|---|---|---|
| `POST` | `/todos` | `{ "title": "..." }` | `201` `{ id, title, completed, created_at }` | Create |
| `GET` | `/todos` | — | `200` `[ { ... } ]` | List all |
| `PATCH` | `/todos/{id}` | `{ "completed": bool }` | `200` `{ ... }` | Toggle complete |
| `DELETE` | `/todos/{id}` | — | `204` | Delete |

CORS is enabled for the Vite dev origin.

## 7. Frontend (React + Vite)

- **Stack:** React, Vite, fetch-based API client (no external state library).
- **Views:** Single page — header, an input + "Add" button, and the list.
- **List item:** title, a checkbox bound to `completed`, and a delete button. Completed todos show strikethrough + muted styling.
- **State:** Todos held in component state; mutating calls optimistically update then reconcile with server response, or refetch on error.
- **Empty state:** Friendly "No todos yet" message.
- **Responsiveness:** Works on mobile and desktop widths.

## 8. Backend (Python FastAPI)

- **Stack:** FastAPI, Pydantic for request/response models, Uvicorn dev server.
- **Persistence:** In-memory list for v1 (swap interface allows a DB later without changing routes).
- **Structure:** `main.py` (app + CORS), `routers/todos.py` (routes), `models.py` (Pydantic schemas), `store.py` (persistence interface + in-memory impl).
- **Startup:** `uvicorn app.main:app --reload`.
- **Docs:** Auto-generated OpenAPI at `/docs`.

## 9. Non-Functional Requirements

- **Performance:** Initial load < 1s on a normal connection; API p99 < 100ms for the in-memory store.
- **Reliability:** Client handles network failures with a retry/error message, never silently drops state.
- **Maintainability:** Typed Pydantic models; clear separation of routes, models, and store.
- **Portability:** Runs on Windows, macOS, Linux with standard toolchains.

## 10. Out of Scope / Future

- Persistence to a database (SQLite/Postgres).
- Auth and per-user lists.
- Editing titles, due dates, priorities, tags.
- Search, filter (all/active/completed), bulk actions.
- Deploy/hosting pipeline.

## 11. Acceptance Criteria

- A user can add a todo and see it appear in the list immediately.
- A user can check a todo and see it styled as complete; unchecking restores it.
- A user can delete a todo and it disappears from the list.
- Reloading the page reflects the latest server state (via GET on mount).
- The API returns correct status codes per §6, and invalid input is rejected with `400`.