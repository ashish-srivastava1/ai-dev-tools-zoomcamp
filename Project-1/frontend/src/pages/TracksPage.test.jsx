import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { api } from '../api/client'
import TracksPage from './TracksPage'

vi.mock('../api/client', async (orig) => {
  const real = await orig()
  return {
    ...real,
    api: {
      listTracks: vi.fn(),
      createTrack: vi.fn(),
      updateTrack: vi.fn(),
      listModules: vi.fn().mockResolvedValue([]),
    },
  }
})

const track = {
  id: 1,
  name: 'Zoomcamp',
  description: null,
  target_hours: 40,
  color: '#4f46e5',
  archived: false,
  created_at: '2026-10-01T00:00:00Z',
}

describe('TracksPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    api.listTracks.mockResolvedValue([track])
  })

  it('creates a track and reloads the list', async () => {
    api.createTrack.mockResolvedValue({ ...track, id: 2, name: 'eMDP' })
    render(<TracksPage />)
    await screen.findByText('Zoomcamp')
    await userEvent.type(screen.getByLabelText('Name'), 'eMDP')
    const target = screen.getByLabelText('Target hours')
    await userEvent.clear(target)
    await userEvent.type(target, '60')
    await userEvent.click(screen.getByRole('button', { name: 'Add track' }))
    await waitFor(() =>
      expect(api.createTrack).toHaveBeenCalledWith({
        name: 'eMDP',
        description: null,
        target_hours: 60,
        color: '#4f46e5',
      }),
    )
    await waitFor(() => expect(api.listTracks).toHaveBeenCalledTimes(2))
  })

  it('archives a track', async () => {
    api.updateTrack.mockResolvedValue({ ...track, archived: true })
    render(<TracksPage />)
    await userEvent.click(await screen.findByRole('button', { name: 'Archive' }))
    expect(api.updateTrack).toHaveBeenCalledWith(1, { archived: true })
  })

  it('requests archived tracks when the toggle is on', async () => {
    render(<TracksPage />)
    await screen.findByText('Zoomcamp')
    await userEvent.click(screen.getByLabelText('Show archived'))
    await waitFor(() => expect(api.listTracks).toHaveBeenLastCalledWith({ includeArchived: true }))
  })

  it('opens the module list for a track', async () => {
    render(<TracksPage />)
    await userEvent.click(await screen.findByRole('button', { name: 'Modules' }))
    expect(await screen.findByText(/No modules yet/)).toBeInTheDocument()
    expect(api.listModules).toHaveBeenCalledWith(1)
  })
})
