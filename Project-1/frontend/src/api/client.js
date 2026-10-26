// The ONLY module that talks to the backend (AGENTS.md rule 3).
// Every page/component imports from here, so tests mock this one file.

const BASE = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')
const TOKEN_KEY = 'learnloop.writeToken'

export class ApiError extends Error {
  constructor(status, message, fieldErrors = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.fieldErrors = fieldErrors
  }
}

export function getWriteToken() {
  try {
    return localStorage.getItem(TOKEN_KEY) || ''
  } catch {
    return ''
  }
}

export function setWriteToken(token) {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token)
    else localStorage.removeItem(TOKEN_KEY)
  } catch {
    /* storage unavailable - token just won't persist */
  }
}

// Turn FastAPI's { detail } into a message + per-field errors.
export function parseError(status, body) {
  const detail = body?.detail
  if (Array.isArray(detail)) {
    const fieldErrors = {}
    for (const item of detail) {
      const loc = (item.loc || []).filter((p) => p !== 'body' && p !== 'query')
      const field = loc.length ? String(loc[loc.length - 1]) : '_'
      const msg = (item.msg || 'invalid').replace(/^Value error, /, '')
      fieldErrors[field] = fieldErrors[field] ? `${fieldErrors[field]}; ${msg}` : msg
    }
    const message = Object.entries(fieldErrors)
      .map(([f, m]) => (f === '_' ? m : `${f}: ${m}`))
      .join(' · ')
    return new ApiError(status, message || 'Validation failed', fieldErrors)
  }
  if (typeof detail === 'string') return new ApiError(status, detail)
  return new ApiError(status, `Request failed (${status})`)
}

async function request(method, path, body) {
  const headers = { Accept: 'application/json' }
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  const token = getWriteToken()
  if (token && method !== 'GET') headers.Authorization = `Bearer ${token}`

  const options = { method, headers }
  if (body !== undefined) options.body = JSON.stringify(body)

  let res
  try {
    res = await fetch(`${BASE}${path}`, options)
  } catch {
    throw new ApiError(0, 'Cannot reach the server. Is the backend running?')
  }
  if (res.status === 204) return null
  const data = await res.json().catch(() => null)
  if (!res.ok) throw parseError(res.status, data)
  return data
}

function qs(params) {
  const q = new URLSearchParams()
  for (const [k, v] of Object.entries(params || {})) {
    if (v !== undefined && v !== null && v !== '') q.set(k, v)
  }
  const s = q.toString()
  return s ? `?${s}` : ''
}

export const api = {
  health: () => request('GET', '/health'),

  // F1 tracks
  listTracks: ({ includeArchived = false } = {}) =>
    request('GET', `/api/tracks${qs({ include_archived: includeArchived || undefined })}`),
  createTrack: (track) => request('POST', '/api/tracks', track),
  updateTrack: (id, changes) => request('PATCH', `/api/tracks/${id}`, changes),

  // F2 modules
  listModules: (trackId) => request('GET', `/api/tracks/${trackId}/modules`),
  createModule: (trackId, module) => request('POST', `/api/tracks/${trackId}/modules`, module),
  updateModule: (id, changes) => request('PATCH', `/api/modules/${id}`, changes),
  deleteModule: (id) => request('DELETE', `/api/modules/${id}`),
  reorderModules: (trackId, moduleIds) =>
    request('PUT', `/api/tracks/${trackId}/modules/order`, { module_ids: moduleIds }),

  // F3 sessions
  listSessions: ({ trackId, from, to, page = 1, pageSize = 20 } = {}) =>
    request(
      'GET',
      `/api/sessions${qs({ track_id: trackId, from, to, page, page_size: pageSize })}`,
    ),
  createSession: (session) => request('POST', '/api/sessions', session),
  updateSession: (id, changes) => request('PATCH', `/api/sessions/${id}`, changes),
  deleteSession: (id) => request('DELETE', `/api/sessions/${id}`),

  // F4 dashboard
  getDashboard: () => request('GET', '/api/dashboard'),

  // F5 settings
  getSettings: () => request('GET', '/api/settings'),
  updateSettings: (settings) => request('PUT', '/api/settings', settings),
}
