import { useState } from 'react'
import { api } from '../api/client'

export default function TrackForm({ initial, onSaved, onCancel }) {
  const [form, setForm] = useState({
    name: initial?.name ?? '',
    description: initial?.description ?? '',
    target_hours: initial?.target_hours ?? 20,
    color: initial?.color ?? '#4f46e5',
  })
  const [error, setError] = useState(null)

  const set = (f) => (e) => setForm({ ...form, [f]: e.target.value })

  async function submit(e) {
    e.preventDefault()
    setError(null)
    const payload = {
      name: form.name.trim(),
      description: form.description.trim() || null,
      target_hours: Number(form.target_hours),
      color: form.color,
    }
    try {
      const saved = initial
        ? await api.updateTrack(initial.id, payload)
        : await api.createTrack(payload)
      if (!initial) setForm({ name: '', description: '', target_hours: 20, color: '#4f46e5' })
      onSaved?.(saved)
    } catch (err) {
      setError(err)
    }
  }

  return (
    <form className="track-form" onSubmit={submit} aria-label={initial ? 'Edit track' : 'New track'}>
      <div className="row">
        <label>
          Name
          <input value={form.name} onChange={set('name')} maxLength={80} required />
        </label>
        <label className="narrow">
          Target hours
          <input
            type="number"
            min="0.5"
            step="0.5"
            value={form.target_hours}
            onChange={set('target_hours')}
            required
          />
        </label>
        <label className="narrow">
          Colour
          <input type="color" value={form.color} onChange={set('color')} />
        </label>
      </div>
      <label>
        Description <span className="muted">(optional)</span>
        <input value={form.description} onChange={set('description')} maxLength={500} />
      </label>
      <div className="actions">
        <button type="submit">{initial ? 'Save track' : 'Add track'}</button>
        {onCancel && (
          <button type="button" className="secondary" onClick={onCancel}>
            Cancel
          </button>
        )}
        {error && (
          <span role="alert" className="error-text">
            {error.message}
          </span>
        )}
      </div>
    </form>
  )
}
