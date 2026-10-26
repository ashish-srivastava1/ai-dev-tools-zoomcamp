import { useEffect, useState } from 'react'
import { api, getWriteToken, setWriteToken } from '../api/client'
import ErrorBanner from '../components/ErrorBanner'

const ZONES = [
  'Asia/Kolkata',
  'Asia/Singapore',
  'Asia/Tokyo',
  'Europe/London',
  'Europe/Berlin',
  'America/New_York',
  'America/Los_Angeles',
  'Australia/Sydney',
  'UTC',
]

export default function SettingsPage() {
  const [form, setForm] = useState(null)
  const [token, setToken] = useState(getWriteToken())
  const [errors, setErrors] = useState({})
  const [error, setError] = useState(null)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    api.getSettings().then(setForm).catch(setError)
  }, [])

  if (!form) return error ? <ErrorBanner error={error} /> : <p className="muted">Loading...</p>

  const set = (f) => (e) => {
    setSaved(false)
    setForm({ ...form, [f]: e.target.value })
  }

  async function submit(e) {
    e.preventDefault()
    setErrors({})
    setError(null)
    setSaved(false)
    setWriteToken(token.trim())
    try {
      const updated = await api.updateSettings({
        weekly_goal_hours: Number(form.weekly_goal_hours),
        timezone: form.timezone.trim(),
        week_start: form.week_start,
      })
      setForm(updated)
      setSaved(true)
    } catch (err) {
      setErrors(err.fieldErrors || {})
      setError(err)
    }
  }

  return (
    <section className="card settings">
      <h1>Settings</h1>
      <form onSubmit={submit} aria-label="Settings">
        <label>
          Weekly goal (hours)
          <input
            type="number"
            min="0.5"
            max="168"
            step="0.5"
            value={form.weekly_goal_hours}
            onChange={set('weekly_goal_hours')}
            required
          />
          {errors.weekly_goal_hours && (
            <span className="field-error">{errors.weekly_goal_hours}</span>
          )}
        </label>
        <label>
          Timezone
          <input list="zones" value={form.timezone} onChange={set('timezone')} required />
          <datalist id="zones">
            {ZONES.map((z) => (
              <option key={z} value={z} />
            ))}
          </datalist>
          {errors.timezone && <span className="field-error">{errors.timezone}</span>}
        </label>
        <label>
          Week starts on
          <select value={form.week_start} onChange={set('week_start')}>
            <option value="monday">Monday</option>
            <option value="sunday">Sunday</option>
          </select>
        </label>
        <label>
          Write token <span className="muted">(only needed on the public demo)</span>
          <input
            type="password"
            autoComplete="off"
            value={token}
            onChange={(e) => setToken(e.target.value)}
          />
        </label>
        <div className="actions">
          <button type="submit">Save settings</button>
          {saved && (
            <span role="status" className="ok-text">
              Saved
            </span>
          )}
        </div>
        <ErrorBanner error={error} />
      </form>
    </section>
  )
}
