# CLAUDE.md — frontend

React + Vite SPA for ClaudeTodo. The shared API contract, project overview, and dev orchestration live in the **root `../CLAUDE.md`** — read that first; this file covers frontend-only specifics.

## Run

```bash
npm install
npm run dev      # :5173, proxies /api -> :8000
npm run build    # production build to dist/
```

There is no test runner and no linter configured.

## Layout (`src/`)

- `src/api.js` — the fetch client. All calls use **relative** `/api/...` URLs.
- `src/App.jsx` — the entire UI and all state. Header + remaining-count, input + Add, list (checkbox + delete), empty state, error banner.
- `src/main.jsx` — mounts `<App/>` in `StrictMode`.
- `vite.config.js` — the `/api` → `http://localhost:8000` proxy (the reason client code uses relative URLs).
- `App.css` / `index.css` — styling; completed todos get strikethrough + muted via `todo-item--done`.

## Conventions that aren't obvious from the code

- **No state library.** State lives in `useState` hooks in `App.jsx`. Don't introduce Redux/Zustand/etc. without a real need.
- **Every mutation is optimistic + reconciling.** Update local state immediately, then either reconcile with the server response (create) or rollback + refetch on error (toggle/delete). When adding a new action, follow this pattern — never block the UI on a pending request, and never silently drop state on failure (show the error banner and refetch).
- **Use relative `/api` URLs only** in `api.js`. The Vite proxy handles dev; relative URLs also work for `vite preview`/built deploys. Hardcoding `http://localhost:8000` breaks the proxy and any non-dev deployment.
- **Errors come back as `{ "detail": "..." }`** — `parseError` in `api.js` extracts `detail` and surfaces it in the error banner. When adding endpoints, keep returning the same shape from the backend.
- **Trim titles client-side before POST** is not required (the backend trims), but the Add button is disabled when the input is empty/whitespace; preserve that UX.