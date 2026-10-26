import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { api, ApiError, getWriteToken } from '../api/client'
import SettingsPage from './SettingsPage'

vi.mock('../api/client', async (orig) => {
  const real = await orig()
  return { ...real, api: { getSettings: vi.fn(), updateSettings: vi.fn() } }
})

describe('SettingsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    api.getSettings.mockResolvedValue({
      weekly_goal_hours: 5,
      timezone: 'Asia/Kolkata',
      week_start: 'monday',
    })
  })

  it('saves settings and stores the write token', async () => {
    api.updateSettings.mockImplementation((s) => Promise.resolve(s))
    render(<SettingsPage />)
    const goal = await screen.findByLabelText('Weekly goal (hours)')
    await userEvent.clear(goal)
    await userEvent.type(goal, '8')
    await userEvent.selectOptions(screen.getByLabelText('Week starts on'), 'sunday')
    await userEvent.type(screen.getByLabelText(/Write token/), 'demo-token')
    await userEvent.click(screen.getByRole('button', { name: 'Save settings' }))
    await waitFor(() =>
      expect(api.updateSettings).toHaveBeenCalledWith({
        weekly_goal_hours: 8,
        timezone: 'Asia/Kolkata',
        week_start: 'sunday',
      }),
    )
    expect(await screen.findByRole('status')).toHaveTextContent('Saved')
    expect(getWriteToken()).toBe('demo-token')
  })

  it('shows validation errors from the API', async () => {
    api.updateSettings.mockRejectedValue(
      new ApiError(422, 'timezone: unknown IANA timezone: Mars/Base', {
        timezone: 'unknown IANA timezone: Mars/Base',
      }),
    )
    render(<SettingsPage />)
    const tz = await screen.findByLabelText('Timezone')
    await userEvent.clear(tz)
    await userEvent.type(tz, 'Mars/Base')
    await userEvent.click(screen.getByRole('button', { name: 'Save settings' }))
    expect(await screen.findByText('unknown IANA timezone: Mars/Base')).toHaveClass('field-error')
  })
})
