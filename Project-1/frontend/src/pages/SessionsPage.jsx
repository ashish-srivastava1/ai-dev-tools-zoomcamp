import { useCallback, useEffect, useState } from 'react'
import { api } from '../api/client'
import ErrorBanner from '../components/ErrorBanner'
import SessionForm from '../components/SessionForm'
import { formatDate, formatMinutes, todayIn } from '../lib/format'

const PAGE_SIZE = 20

export default function SessionsPage() {
  const [tracks, setTracks] = useState([])
  const [allTracks, setAllTracks] = useState([])
  const [today, setToday] = useState(todayIn('Asia/Kolkata'))
  const [filters, setFilters] = useState({ trackId: '', from: '', to: '' })
  const [page, setPage] = useState(1)
  const [data, setData] = useState({ items: [], total: 0 })
  const [editing, setEditing] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    Promise.all([api.listTracks(), api.listTracks({ includeArchived: true }), api.getSettings()])
      .then(([active, all, settings]) => {
        setTracks(active)
        setAllTracks(all)
        setToday(todayIn(settings.timezone))
      })
      .catch(setError)
  }, [])

  const load = useCallback(
    () =>
      api
        .listSessions({ ...filters, page, pageSize: PAGE_SIZE })
        .then((d) => {
          setData(d)
          setError(null)
        })
        .catch(setError),
    [filters, page],
  )
  useEffect(() => {
    load()
  }, [load])

  const setFilter = (key) => (e) => {
    setPage(1)
    setFilters((f) => ({ ...f, [key]: e.target.value }))
  }

  async function remove(s) {
    try {
      await api.deleteSession(s.id)
      await load()
    } catch (err) {
      setError(err)
    }
  }

  const trackName = Object.fromEntries(allTracks.map((t) => [t.id, t.name]))
  const pages = Math.max(1, Math.ceil(data.total / PAGE_SIZE))

  return (
    <div className="sessions-page">
      <section className="card">
        <h1>Log a session</h1>
        <SessionForm tracks={tracks} today={today} onSaved={load} />
      </section>

      <section className="card">
        <h2>Sessions</h2>
        <div className="filters row">
          <label>
            Track
            <select value={filters.trackId} onChange={setFilter('trackId')} aria-label="Filter by track">
              <option value="">All tracks</option>
              {allTracks.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            From
            <input type="date" value={filters.from} onChange={setFilter('from')} />
          </label>
          <label>
            To
            <input type="date" value={filters.to} onChange={setFilter('to')} />
          </label>
        </div>
        <ErrorBanner error={error} />
        {!data.items.length && <p className="muted">No sessions match.</p>}
        <ul className="session-list">
          {data.items.map((s) =>
            editing === s.id ? (
              <li key={s.id} className="editing">
                <SessionForm
                  tracks={allTracks}
                  today={today}
                  initial={s}
                  onSaved={() => {
                    setEditing(null)
                    load()
                  }}
                  onCancel={() => setEditing(null)}
                />
              </li>
            ) : (
              <li key={s.id}>
                <span className="muted">{formatDate(s.date)}</span>
                <strong>{s.topic}</strong>
                <span>{trackName[s.track_id] ?? ''}</span>
                <span className="muted">{formatMinutes(s.minutes)}</span>
                <span className="row-actions">
                  <button type="button" className="secondary" onClick={() => setEditing(s.id)}>
                    Edit
                  </button>
                  <button type="button" className="secondary danger" onClick={() => remove(s)}>
                    Delete
                  </button>
                </span>
              </li>
            ),
          )}
        </ul>
        <div className="pager">
          <button
            type="button"
            className="secondary"
            disabled={page <= 1}
            onClick={() => setPage(page - 1)}
          >
            ← Prev
          </button>
          <span className="muted">
            Page {page} of {pages} · {data.total} sessions
          </span>
          <button
            type="button"
            className="secondary"
            disabled={page >= pages}
            onClick={() => setPage(page + 1)}
          >
            Next →
          </button>
        </div>
      </section>
    </div>
  )
}
