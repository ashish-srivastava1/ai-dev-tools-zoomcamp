import { useCallback, useEffect, useState } from 'react'
import { api } from '../api/client'
import ErrorBanner from '../components/ErrorBanner'
import ModuleList from '../components/ModuleList'
import TrackForm from '../components/TrackForm'
import { formatHours } from '../lib/format'

export default function TracksPage() {
  const [tracks, setTracks] = useState([])
  const [showArchived, setShowArchived] = useState(false)
  const [editing, setEditing] = useState(null)
  const [open, setOpen] = useState(null)
  const [error, setError] = useState(null)

  const load = useCallback(
    () =>
      api
        .listTracks({ includeArchived: showArchived })
        .then((t) => {
          setTracks(t)
          setError(null)
        })
        .catch(setError),
    [showArchived],
  )
  useEffect(() => {
    load()
  }, [load])

  async function toggleArchive(t) {
    try {
      await api.updateTrack(t.id, { archived: !t.archived })
      await load()
    } catch (err) {
      setError(err)
    }
  }

  return (
    <div className="tracks-page">
      <section className="card">
        <h1>New track</h1>
        <TrackForm onSaved={load} />
      </section>

      <section className="card">
        <div className="section-head">
          <h2>Your tracks</h2>
          <label className="checkbox">
            <input
              type="checkbox"
              checked={showArchived}
              onChange={(e) => setShowArchived(e.target.checked)}
            />
            Show archived
          </label>
        </div>
        <ErrorBanner error={error} />
        {!tracks.length && <p className="muted">No tracks yet.</p>}
        <ul className="track-list">
          {tracks.map((t) => (
            <li key={t.id} className={t.archived ? 'archived' : ''}>
              {editing === t.id ? (
                <TrackForm
                  initial={t}
                  onSaved={() => {
                    setEditing(null)
                    load()
                  }}
                  onCancel={() => setEditing(null)}
                />
              ) : (
                <div className="track-row">
                  <span className="swatch" style={{ background: t.color }} />
                  <div className="track-info">
                    <strong>{t.name}</strong>
                    {t.archived && <span className="badge">archived</span>}
                    <span className="muted small">
                      Target {formatHours(t.target_hours)}
                      {t.description ? ` · ${t.description}` : ''}
                    </span>
                  </div>
                  <div className="row-actions">
                    <button
                      type="button"
                      className="secondary"
                      onClick={() => setOpen(open === t.id ? null : t.id)}
                      aria-expanded={open === t.id}
                    >
                      Modules
                    </button>
                    <button type="button" className="secondary" onClick={() => setEditing(t.id)}>
                      Edit
                    </button>
                    <button type="button" className="secondary" onClick={() => toggleArchive(t)}>
                      {t.archived ? 'Unarchive' : 'Archive'}
                    </button>
                  </div>
                </div>
              )}
              {open === t.id && <ModuleList trackId={t.id} />}
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}
