import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { api } from '../api/client'
import DashboardPage from './DashboardPage'

vi.mock('../api/client', async (orig) => {
  const real = await orig()
  return {
    ...real,
    api: {
      getDashboard: vi.fn(),
      listTracks: vi.fn(),
      listModules: vi.fn().mockResolvedValue([]),
      createSession: vi.fn(),
    },
  }
})

const trend = Array.from({ length: 8 }, (_, i) => ({
  week_start: `2026-09-${String(i * 7 + 1).padStart(2, '0')}`,
  hours: i,
}))

function dashboard(overrides = {}) {
  return {
    empty: false,
    today: '2026-10-21',
    timezone: 'Asia/Kolkata',
    week: { start: '2026-10-19', hours: 2.5, goal_hours: 5, percent: 50 },
    streak: { current_days: 3, longest_days: 7 },
    tracks: [
      {
        track_id: 1,
        name: 'Zoomcamp',
        color: '#4f46e5',
        hours: 10,
        target_hours: 40,
        target_percent: 25,
        module_count: 4,
        completion_percent: 50,
      },
    ],
    weekly_trend: trend,
    recent_sessions: [
      {
        id: 9,
        track_id: 1,
        module_id: null,
        date: '2026-10-21',
        minutes: 90,
        topic: 'Grafana alerts',
        notes: null,
        created_at: '2026-10-21T10:00:00Z',
      },
    ],
    ...overrides,
  }
}

const renderPage = () =>
  render(
    <MemoryRouter>
      <DashboardPage />
    </MemoryRouter>,
  )

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    api.listTracks.mockResolvedValue([{ id: 1, name: 'Zoomcamp' }])
  })

  it('shows the empty state with a link to create a track', async () => {
    api.getDashboard.mockResolvedValue(dashboard({ empty: true, tracks: [] }))
    api.listTracks.mockResolvedValue([])
    renderPage()
    const link = await screen.findByRole('link', { name: /create your first track/i })
    expect(link).toHaveAttribute('href', '/tracks')
  })

  it('renders weekly progress, streaks, tracks, trend and recent sessions', async () => {
    api.getDashboard.mockResolvedValue(dashboard())
    renderPage()
    expect(await screen.findByTestId('week-hours')).toHaveTextContent('2.5 h')
    expect(screen.getByText('50% of weekly goal')).toBeInTheDocument()
    expect(screen.getByTestId('current-streak')).toHaveTextContent('3 days')
    expect(screen.getByText('Longest: 7 days')).toBeInTheDocument()
    expect(screen.getByText(/10 h of 40 h \(25%\)/)).toBeInTheDocument()
    expect(screen.getByText(/Modules: 50% complete/)).toBeInTheDocument()
    expect(screen.getAllByTestId('trend-bar')).toHaveLength(8)
    expect(screen.getByText('Grafana alerts')).toBeInTheDocument()
  })

  it('re-fetches the dashboard after a session is logged (AC3.1)', async () => {
    api.getDashboard
      .mockResolvedValueOnce(dashboard())
      .mockResolvedValueOnce(
        dashboard({ week: { start: '2026-10-19', hours: 3, goal_hours: 5, percent: 60 } }),
      )
    api.createSession.mockResolvedValue({ id: 10 })
    renderPage()
    await screen.findByTestId('week-hours')
    await userEvent.type(screen.getByLabelText('Topic'), 'Tempo')
    await userEvent.click(screen.getByRole('button', { name: 'Log session' }))
    await waitFor(() => expect(api.getDashboard).toHaveBeenCalledTimes(2))
    expect(await screen.findByText('60% of weekly goal')).toBeInTheDocument()
  })

  it('shows an error when the API is down', async () => {
    api.getDashboard.mockRejectedValue(new Error('Cannot reach the server'))
    renderPage()
    expect(await screen.findByRole('alert')).toHaveTextContent('Cannot reach the server')
  })
})
