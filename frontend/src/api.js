// Fetch-based API client (PRD §7). Base path /api is proxied to the FastAPI
// dev server by Vite (see vite.config.js), so relative URLs work in both dev
// and preview builds.

// In dev, Vite proxies /api to the backend. In production (Render), VITE_API_URL
// is the backend's public hostname (without the https:// scheme) and we build
// an absolute https:// URL. Empty/unset means "use same-origin /api".
const API_HOST = import.meta.env.VITE_API_URL || "";
const BASE = API_HOST ? `https://${API_HOST}/api` : "/api";

// The fixed category set. Kept in sync with the backend's CATEGORIES
// (backend/app/models.py). Category is immutable after creation, so the
// picker only ever sends one of these. "All" is a filter-only sentinel, never
// sent to the server.
export const CATEGORIES = ["General", "Work", "Personal", "Shopping", "Health"];
export const FILTER_ALL = "All";
export const DEFAULT_CATEGORY = CATEGORIES[0];

async function parseError(res) {
  // Errors are JSON of the form { "detail": "..." } (PRD §5.3).
  try {
    const body = await res.json();
    return body.detail || `Request failed (${res.status})`;
  } catch {
    return `Request failed (${res.status})`;
  }
}

export async function listTodos() {
  const res = await fetch(`${BASE}/todos`);
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function createTodo(title, category) {
  const res = await fetch(`${BASE}/todos`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, category }),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function updateTodo(id, completed) {
  // Category is immutable after creation; PATCH only toggles `completed`.
  const res = await fetch(`${BASE}/todos/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ completed }),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function deleteTodo(id) {
  const res = await fetch(`${BASE}/todos/${id}`, { method: "DELETE" });
  // 204 on success, idempotent for missing ids (PRD §5.2).
  if (!res.ok && res.status !== 204) throw new Error(await parseError(res));
}
