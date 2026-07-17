// Fetch-based API client (PRD §7). Base path /api is proxied to the FastAPI
// dev server by Vite (see vite.config.js), so relative URLs work in both dev
// and preview builds.

const BASE = '/api'

async function parseError(res) {
  // Errors are JSON of the form { "detail": "..." } (PRD §5.3).
  try {
    const body = await res.json()
    return body.detail || `Request failed (${res.status})`
  } catch {
    return `Request failed (${res.status})`
  }
}

export async function listTodos() {
  const res = await fetch(`${BASE}/todos`)
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function createTodo(title) {
  const res = await fetch(`${BASE}/todos`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function updateTodo(id, completed) {
  const res = await fetch(`${BASE}/todos/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ completed }),
  })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function deleteTodo(id) {
  const res = await fetch(`${BASE}/todos/${id}`, { method: 'DELETE' })
  // 204 on success, idempotent for missing ids (PRD §5.2).
  if (!res.ok && res.status !== 204) throw new Error(await parseError(res))
}