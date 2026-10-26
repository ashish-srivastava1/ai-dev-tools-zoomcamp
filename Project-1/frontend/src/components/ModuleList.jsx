import { useCallback, useEffect, useState } from 'react'
import { api } from '../api/client'

const STATUS_LABEL = { not_started: 'Not started', in_progress: 'In progress', done: 'Done' }

export default function ModuleList({ trackId }) {
  const [modules, setModules] = useState([])
  const [title, setTitle] = useState('')
  const [error, setError] = useState(null)

  const load = useCallback(
    () => api.listModules(trackId).then(setModules).catch(setError),
    [trackId],
  )
  useEffect(() => {
    load()
  }, [load])

  const run = (fn) => async (...args) => {
    setError(null)
    try {
      await fn(...args)
      await load()
    } catch (err) {
      setError(err)
    }
  }

  const add = run(async (e) => {
    e.preventDefault()
    await api.createModule(trackId, { title: title.trim() })
    setTitle('')
  })
  const setStatus = run((m, status) => api.updateModule(m.id, { status }))
  const remove = run((m) => api.deleteModule(m.id))
  const move = run((index, delta) => {
    const ids = modules.map((m) => m.id)
    const [id] = ids.splice(index, 1)
    ids.splice(index + delta, 0, id)
    return api.reorderModules(trackId, ids)
  })

  const done = modules.filter((m) => m.status === 'done').length
  return (
    <div className="modules">
      <p className="muted">
        {modules.length
          ? `${done} of ${modules.length} modules done`
          : 'No modules yet - break the track into modules to track completion.'}
      </p>
      <ol className="module-list">
        {modules.map((m, i) => (
          <li key={m.id} className={`module status-${m.status}`}>
            <span className="module-title">{m.title}</span>
            <select
              aria-label={`Status of ${m.title}`}
              value={m.status}
              onChange={(e) => setStatus(m, e.target.value)}
            >
              {Object.entries(STATUS_LABEL).map(([v, l]) => (
                <option key={v} value={v}>
                  {l}
                </option>
              ))}
            </select>
            <button
              type="button"
              className="icon"
              aria-label={`Move ${m.title} up`}
              disabled={i === 0}
              onClick={() => move(i, -1)}
            >
              ↑
            </button>
            <button
              type="button"
              className="icon"
              aria-label={`Move ${m.title} down`}
              disabled={i === modules.length - 1}
              onClick={() => move(i, 1)}
            >
              ↓
            </button>
            <button
              type="button"
              className="icon danger"
              aria-label={`Delete ${m.title}`}
              onClick={() => remove(m)}
            >
              ✕
            </button>
          </li>
        ))}
      </ol>
      <form className="inline-form" onSubmit={add}>
        <input
          aria-label="New module title"
          placeholder="New module title"
          value={title}
          maxLength={120}
          onChange={(e) => setTitle(e.target.value)}
          required
        />
        <button type="submit">Add module</button>
      </form>
      {error && (
        <p role="alert" className="error-text">
          {error.message}
        </p>
      )}
    </div>
  )
}
