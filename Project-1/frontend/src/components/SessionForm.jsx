import { useEffect, useState } from 'react'
import { api } from '../api/client'

const empty = (today, trackId) => ({
  track_id: trackId ?? '',
  module_id: '',
  date: today,
  minutes: 30,
  topic: '',
  notes: '',
})

// Used for logging a new session (key journey) and editing an existing one.
export default function SessionForm({ tracks, today, initial, onSaved, onCancel }) {
  const [form, setForm] = useState(() =>
    initial
      ? { ...initial, module_id: initial.module_id ?? '', notes: initial.notes ?? '' }
      : empty(today, tracks[0]?.id),
  )
  const [modules, setModules] = useState([])
  const [errors, setErrors] = useState({})
  const [message, setMessage] = useState('')
  const [saving, setSaving] = useState(false)
  const [ok, setOk] = useState(false)

  useEffect(() => {
    if (!initial && !form.track_id && tracks[0]) {
      setForm((f) => ({ ...f, track_id: tracks[0].id }))
    }
  }, [tracks, initial, form.track_id])

  useEffect(() => {
    let live = true
    if (!form.track_id) {
      setModules([])
      return undefined
    }
    api
      .listModules(form.track_id)
      .then((m) => live && setModules(m))
      .catch(() => live && setModules([]))
    return () => {
      live = false
    }
  }, [form.track_id])

  const set = (field) => (e) => {
    const value = e.target.value
    setForm((f) => ({
      ...f,
      [field]: value,
      ...(field === 'track_id' ? { module_id: '' } : {}),
    }))
  }

  async function submit(e) {
    e.preventDefault()
    setSaving(true)
    setErrors({})
    setMessage('')
    setOk(false)
    const payload = {
      track_id: Number(form.track_id),
      module_id: form.module_id === '' ? null : Number(form.module_id),
      date: form.date,
      minutes: Number(form.minutes),
      topic: form.topic.trim(),
      notes: form.notes.trim() ? form.notes.trim() : null,
    }
    try {
      const saved = initial
        ? await api.updateSession(initial.id, payload)
        : await api.createSession(payload)
      if (!initial) setForm(empty(today, form.track_id))
      setMessage(initial ? 'Session updated' : 'Session logged')
      setOk(true)
      onSaved?.(saved)
    } catch (err) {
      setErrors(err.fieldErrors || {})
      setMessage(err.message)
    } finally {
      setSaving(false)
    }
  }

  if (!tracks.length) {
    return <p className="muted">Create a track first, then log your study sessions.</p>
  }

  return (
    <form
      className="session-form"
      onSubmit={submit}
      aria-label={initial ? 'Edit session' : 'Log session'}
    >
      <div className="row">
        <label>
          Track
          <select value={form.track_id} onChange={set('track_id')} required>
            {tracks.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
          <FieldError msg={errors.track_id} />
        </label>
        <label>
          Module <span className="muted">(optional)</span>
          <select value={form.module_id} onChange={set('module_id')}>
            <option value="">-</option>
            {modules.map((m) => (
              <option key={m.id} value={m.id}>
                {m.title}
              </option>
            ))}
          </select>
          <FieldError msg={errors.module_id} />
        </label>
      </div>
      <div className="row">
        <label>
          Date
          <input type="date" value={form.date} max={today} onChange={set('date')} required />
          <FieldError msg={errors.date} />
        </label>
        <label>
          Minutes
          <input
            type="number"
            min="1"
            max="600"
            value={form.minutes}
            onChange={set('minutes')}
            required
          />
          <FieldError msg={errors.minutes} />
        </label>
      </div>
      <label>
        Topic
        <input
          value={form.topic}
          onChange={set('topic')}
          maxLength={120}
          placeholder="e.g. Docker Compose healthchecks"
          required
        />
        <FieldError msg={errors.topic} />
      </label>
      <label>
        Notes <span className="muted">(optional)</span>
        <textarea value={form.notes} onChange={set('notes')} maxLength={2000} rows={2} />
        <FieldError msg={errors.notes} />
      </label>
      <div className="actions">
        <button type="submit" disabled={saving}>
          {saving ? 'Saving...' : initial ? 'Save changes' : 'Log session'}
        </button>
        {onCancel && (
          <button type="button" className="secondary" onClick={onCancel}>
            Cancel
          </button>
        )}
        {message && (
          <span role="status" className={ok ? 'ok-text' : 'error-text'}>
            {message}
          </span>
        )}
      </div>
    </form>
  )
}

function FieldError({ msg }) {
  return msg ? <span className="field-error">{msg}</span> : null
}
