export function formatHours(h) {
  const n = Number(h) || 0
  if (n === 0) return '0 h'
  if (n < 1) return `${Math.round(n * 60)} min`
  return `${Number.isInteger(n) ? n : n.toFixed(1)} h`
}

export function formatMinutes(m) {
  const n = Number(m) || 0
  const h = Math.floor(n / 60)
  const mins = n % 60
  if (!h) return `${mins} min`
  return mins ? `${h} h ${mins} min` : `${h} h`
}

export function formatDate(iso) {
  if (!iso) return ''
  const [y, m, d] = iso.split('-').map(Number)
  return new Date(Date.UTC(y, m - 1, d)).toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    timeZone: 'UTC',
  })
}

export function shortWeek(iso) {
  const [y, m, d] = iso.split('-').map(Number)
  return new Date(Date.UTC(y, m - 1, d)).toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    timeZone: 'UTC',
  })
}

// YYYY-MM-DD for "today" in an IANA timezone.
export function todayIn(timeZone, now = new Date()) {
  return new Intl.DateTimeFormat('en-CA', { timeZone }).format(now)
}

export function clampPercent(p) {
  return Math.max(0, Math.min(100, Number(p) || 0))
}
