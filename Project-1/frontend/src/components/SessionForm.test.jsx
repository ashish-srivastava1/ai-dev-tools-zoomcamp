import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { api, ApiError } from '../api/client'
import SessionForm from './SessionForm'

vi.mock('../api/client', async (orig) => {
  const real = await orig()
  return {
    ...real,
    api: { listModules: vi.fn(), createSession: vi.fn(), updateSession: vi.fn() },
  }
})

const tracks = [
  { id: 1, name: 'Zoomcamp' },
  { id: 2, name: 'eMDP' },
]

describe('SessionForm', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    api.listModules.mockImplementation((id) =>
      Promise.resolve(id === 1 ? [{ id: 11, title: 'Docker' }] : [{ id: 21, title: 'Stats' }]),
    )
  })

  it('loads modules for the selected track', async () => {
    render(<SessionForm tracks={tracks} today="2026-10-21" />)
    expect(await screen.findByRole('option', { name: 'Docker' })).toBeInTheDocument()
    await userEvent.selectOptions(screen.getByLabelText('Track'), '2')
    expect(await screen.findByRole('option', { name: 'Stats' })).toBeInTheDocument()
    expect(api.listModules).toHaveBeenLastCalledWith('2')
  })

  it('submits the correct payload and calls onSaved', async () => {
    api.createSession.mockResolvedValue({ id: 5 })
    const onSaved = vi.fn()
    render(<SessionForm tracks={tracks} today="2026-10-21" onSaved={onSaved} />)
    await screen.findByRole('option', { name: 'Docker' })
    await userEvent.selectOptions(screen.getByLabelText(/Module/), '11')
    const minutes = screen.getByLabelText('Minutes')
    await userEvent.clear(minutes)
    await userEvent.type(minutes, '45')
    await userEvent.type(screen.getByLabelText('Topic'), '  Compose healthchecks ')
    await userEvent.click(screen.getByRole('button', { name: 'Log session' }))

    await waitFor(() => expect(onSaved).toHaveBeenCalledWith({ id: 5 }))
    expect(api.createSession).toHaveBeenCalledWith({
      track_id: 1,
      module_id: 11,
      date: '2026-10-21',
      minutes: 45,
      topic: 'Compose healthchecks',
      notes: null,
    })
    expect(screen.getByRole('status')).toHaveTextContent('Session logged')
  })

  it('shows field errors returned by the API', async () => {
    api.createSession.mockRejectedValue(
      new ApiError(422, 'date: date cannot be in the future', {
        date: 'date cannot be in the future',
      }),
    )
    render(<SessionForm tracks={tracks} today="2026-10-21" />)
    await userEvent.type(screen.getByLabelText('Topic'), 'x')
    await userEvent.click(screen.getByRole('button', { name: 'Log session' }))
    expect(await screen.findByText('date cannot be in the future')).toHaveClass('field-error')
  })

  it('edits an existing session with updateSession', async () => {
    api.updateSession.mockResolvedValue({ id: 7 })
    const initial = {
      id: 7,
      track_id: 2,
      module_id: null,
      date: '2026-10-20',
      minutes: 30,
      topic: 'Old',
      notes: null,
    }
    render(<SessionForm tracks={tracks} today="2026-10-21" initial={initial} />)
    await userEvent.click(screen.getByRole('button', { name: 'Save changes' }))
    await waitFor(() => expect(api.updateSession).toHaveBeenCalled())
    expect(api.updateSession.mock.calls[0][0]).toBe(7)
    expect(api.updateSession.mock.calls[0][1]).toMatchObject({ track_id: 2, topic: 'Old' })
  })

  it('asks for a track when there are none', () => {
    render(<SessionForm tracks={[]} today="2026-10-21" />)
    expect(screen.getByText(/Create a track first/)).toBeInTheDocument()
  })
})
