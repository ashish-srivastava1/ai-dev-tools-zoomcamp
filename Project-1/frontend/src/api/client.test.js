import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { api, ApiError, getWriteToken, parseError, setWriteToken } from './client'

function mockFetch(status, body) {
  const fn = vi.fn().mockResolvedValue({
    status,
    ok: status >= 200 && status < 300,
    json: () => (body === undefined ? Promise.reject(new Error('no body')) : Promise.resolve(body)),
  })
  globalThis.fetch = fn
  return fn
}

describe('api client', () => {
  beforeEach(() => localStorage.clear())
  afterEach(() => vi.restoreAllMocks())

  it('builds GET paths with query params and skips empty ones', async () => {
    const f = mockFetch(200, { items: [], total: 0, page: 2, page_size: 20 })
    await api.listSessions({ trackId: 3, from: '2026-10-01', to: '', page: 2 })
    expect(f.mock.calls[0][0]).toBe('/api/sessions?track_id=3&from=2026-10-01&page=2&page_size=20')
    expect(f.mock.calls[0][1].method).toBe('GET')
  })

  it('include_archived only when requested', async () => {
    const f = mockFetch(200, [])
    await api.listTracks()
    await api.listTracks({ includeArchived: true })
    expect(f.mock.calls[0][0]).toBe('/api/tracks')
    expect(f.mock.calls[1][0]).toBe('/api/tracks?include_archived=true')
  })

  it('sends JSON body and bearer token only on writes', async () => {
    setWriteToken('abc')
    const f = mockFetch(201, { id: 1 })
    await api.createTrack({ name: 'A', target_hours: 1 })
    const [, opts] = f.mock.calls[0]
    expect(opts.method).toBe('POST')
    expect(opts.headers.Authorization).toBe('Bearer abc')
    expect(opts.headers['Content-Type']).toBe('application/json')
    expect(JSON.parse(opts.body)).toEqual({ name: 'A', target_hours: 1 })

    await api.getDashboard()
    expect(f.mock.calls[1][1].headers.Authorization).toBeUndefined()
  })

  it('reorder sends module_ids', async () => {
    const f = mockFetch(200, [])
    await api.reorderModules(4, [3, 1, 2])
    expect(f.mock.calls[0][0]).toBe('/api/tracks/4/modules/order')
    expect(JSON.parse(f.mock.calls[0][1].body)).toEqual({ module_ids: [3, 1, 2] })
  })

  it('returns null on 204', async () => {
    mockFetch(204)
    expect(await api.deleteSession(9)).toBeNull()
  })

  it('throws ApiError with string detail', async () => {
    mockFetch(422, { detail: 'date cannot be in the future' })
    await expect(api.createSession({})).rejects.toMatchObject({
      name: 'ApiError',
      status: 422,
      message: 'date cannot be in the future',
    })
  })

  it('throws ApiError when the network fails', async () => {
    globalThis.fetch = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'))
    const err = await api.getDashboard().catch((e) => e)
    expect(err).toBeInstanceOf(ApiError)
    expect(err.status).toBe(0)
  })

  it('token helpers round-trip', () => {
    setWriteToken('t1')
    expect(getWriteToken()).toBe('t1')
    setWriteToken('')
    expect(getWriteToken()).toBe('')
  })
})

describe('parseError', () => {
  it('maps FastAPI validation list to field errors', () => {
    const err = parseError(422, {
      detail: [
        { loc: ['body', 'minutes'], msg: 'Input should be less than or equal to 600' },
        { loc: ['body'], msg: 'Value error, at least one field must be provided' },
      ],
    })
    expect(err.fieldErrors.minutes).toBe('Input should be less than or equal to 600')
    expect(err.fieldErrors._).toBe('at least one field must be provided')
    expect(err.message).toContain('minutes:')
  })

  it('falls back to a generic message', () => {
    expect(parseError(500, null).message).toBe('Request failed (500)')
  })
})
