import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import ErrorBanner from '../components/ErrorBanner'
import ProgressBar from '../components/ProgressBar'
import SessionForm from '../components/SessionForm'
import TrendChart from '../components/TrendChart'
import { formatDate, formatHours, formatMinutes } from '../lib/format'

export default function DashboardPage() {
  const [dash, setDash] = useState(null)
  const [tracks, setTracks] = useState([])
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    try {
      const [d, t] = await Promise.all([api.getDashboard(), api.listTracks()])
      setDash(d)
      setTracks(t)
      setError(null)
    } catch (err) {
      setError(err)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  if (error && !dash) return <ErrorBanner error={error} />
  if (!dash) return <p className="muted">Loading...</p>

  if (dash.empty) {
    return (
      <section className="card empty-state">
        <h1>Welcome to LearnLoop</h1>
        <p>Start by creating a learning track, for example a course you are doing.</p>
        <Link className="button" to="/tracks">
          Create your first track
        </Link>
      </section>
    )
  }

  const trackName = Object.fromEntries(tracks.map((t) => [t.id, t.name]))

  return (
    <div className="dashboard">
      <ErrorBanner error={error} />
      <section className="stats">
        <div className="card stat">
          <h2>This week</h2>
          <p className="stat-value" data-testid="week-hours">
            {formatHours(dash.week.hours)}
            <span className="muted"> / {formatHours(dash.week.goal_hours)}</span>
          </p>
          <ProgressBar percent={dash.week.percent} label="Weekly goal progress" />
          <p className="muted">{dash.week.percent}% of weekly goal</p>
        </div>
        <div className="card stat">
          <h2>Current streak</h2>
          <p className="stat-value" data-testid="current-streak">
            {dash.streak.current_days} {dash.streak.current_days === 1 ? 'day' : 'days'}
          </p>
          <p className="muted">Longest: {dash.streak.longest_days} days</p>
        </div>
      </section>

      <section className="card">
        <h2>Log a session</h2>
        <SessionForm tracks={tracks} today={dash.today} onSaved={load} />
      </section>

      <section className="card">
        <h2>Tracks</h2>
        <ul className="track-progress">
          {dash.tracks.map((t) => (
            <li key={t.track_id}>
              <div className="track-progress-head">
                <span className="swatch" style={{ background: t.color }} />
                <strong>{t.name}</strong>
                <span className="muted">
                  {formatHours(t.hours)} of {formatHours(t.target_hours)} ({t.target_percent}%)
                </span>
              </div>
              <ProgressBar percent={t.target_percent} color={t.color} label={`${t.name} hours`} />
              <p className="muted small">
                {t.module_count
                  ? `Modules: ${t.completion_percent}% complete (${t.module_count} modules)`
                  : 'No modules yet'}
              </p>
            </li>
          ))}
        </ul>
      </section>

      <section className="card">
        <h2>Last 8 weeks</h2>
        <TrendChart weeks={dash.weekly_trend} />
      </section>

      <section className="card">
        <h2>Recent sessions</h2>
        {dash.recent_sessions.length ? (
          <ul className="session-list">
            {dash.recent_sessions.map((s) => (
              <li key={s.id}>
                <span className="muted">{formatDate(s.date)}</span>
                <strong>{s.topic}</strong>
                <span>{trackName[s.track_id] ?? ''}</span>
                <span className="muted">{formatMinutes(s.minutes)}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted">No sessions yet - log your first one above.</p>
        )}
        <Link to="/sessions">All sessions →</Link>
      </section>
    </div>
  )
}
