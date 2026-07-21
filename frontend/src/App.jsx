import { useCallback, useEffect, useRef, useState } from 'react'
import {
  CATEGORIES,
  DEFAULT_CATEGORY,
  FILTER_ALL,
  createTodo,
  deleteTodo,
  listTodos,
  updateTodo,
} from './api'
import './App.css'

function App() {
  const [todos, setTodos] = useState([])
  const [title, setTitle] = useState('')
  const [category, setCategory] = useState(DEFAULT_CATEGORY)
  const [filter, setFilter] = useState(FILTER_ALL)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const inputRef = useRef(null)

  // Hydrate from server on mount (PRD §11 — reload reflects latest state).
  const refresh = useCallback(async () => {
    setError(null)
    try {
      setTodos(await listTodos())
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  const handleAdd = async (e) => {
    e.preventDefault()
    const trimmed = title.trim()
    if (!trimmed) return // reject empty/whitespace (PRD §5.2)

    setSubmitting(true)
    setError(null)
    try {
      // Optimistic: show the new todo first, then reconcile with server.
      const created = await createTodo(trimmed, category)
      setTodos((prev) => [created, ...prev])
      setTitle('')
      setCategory(DEFAULT_CATEGORY)
      inputRef.current?.focus()
    } catch (err) {
      setError(err.message)
      // Reconcile from server on error so we never show stale state.
      refresh()
    } finally {
      setSubmitting(false)
    }
  }

  const handleToggle = async (id, completed) => {
    const next = !completed
    // Optimistic update, rollback on failure.
    setTodos((prev) =>
      prev.map((t) => (t.id === id ? { ...t, completed: next } : t)),
    )
    setError(null)
    try {
      await updateTodo(id, next)
    } catch (err) {
      setError(err.message)
      refresh()
    }
  }

  const handleDelete = async (id) => {
    const snapshot = todos
    setTodos((prev) => prev.filter((t) => t.id !== id))
    setError(null)
    try {
      await deleteTodo(id)
    } catch (err) {
      setError(err.message)
      setTodos(snapshot) // rollback
    }
  }

  const activeCount = todos.filter((t) => !t.completed).length
  // Filtering is client-side: the full list is already loaded on mount, so the
  // visible list is a derived view. Totals stay computed from the full list so
  // the header summary doesn't jump when a filter is applied.
  const visible =
    filter === FILTER_ALL ? todos : todos.filter((t) => t.category === filter)

  return (
    <div className="app">
      <header className="app__header">
        <h1 className="app__title">ClaudeTodo</h1>
        <p className="app__subtitle">
          {loading ? 'Loading…' : `${activeCount} of ${todos.length} remaining`}
        </p>
      </header>

      {error && (
        <div className="app__error" role="alert">
          {error}
          <button className="app__error-dismiss" onClick={() => setError(null)}>
            ✕
          </button>
        </div>
      )}

      <form className="app__form" onSubmit={handleAdd}>
        <input
          ref={inputRef}
          className="app__input"
          type="text"
          maxLength={255}
          placeholder="What needs to be done?"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          disabled={submitting}
          aria-label="Todo title"
        />
        <select
          className="app__select"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          disabled={submitting}
          aria-label="Category"
        >
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
        <button className="app__add" type="submit" disabled={submitting || !title.trim()}>
          Add
        </button>
      </form>

      <div className="app__filter">
        <label className="app__filter-label" htmlFor="filter">
          Filter:
        </label>
        <select
          id="filter"
          className="app__select"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          aria-label="Filter by category"
        >
          <option value={FILTER_ALL}>All</option>
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </div>

      {todos.length === 0 ? (
        <p className="app__empty">No todos yet</p>
      ) : visible.length === 0 ? (
        <p className="app__empty">No todos in this category</p>
      ) : (
        <ul className="todo-list">
          {visible.map((todo) => (
            <li key={todo.id} className={`todo-item${todo.completed ? ' todo-item--done' : ''}`}>
              <label className="todo-item__check">
                <input
                  type="checkbox"
                  checked={todo.completed}
                  onChange={() => handleToggle(todo.id, todo.completed)}
                />
                <span className="todo-item__title">{todo.title}</span>
              </label>
              <button
                className="todo-item__delete"
                onClick={() => handleDelete(todo.id)}
                aria-label={`Delete "${todo.title}"`}
                title="Delete"
              >
                ✕
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default App