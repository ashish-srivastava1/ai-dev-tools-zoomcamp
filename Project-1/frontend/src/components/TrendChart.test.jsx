import { render, screen } from '@testing-library/react'
import { expect, it } from 'vitest'
import TrendChart from './TrendChart'

it('renders one bar per week scaled to the max', () => {
  const weeks = Array.from({ length: 8 }, (_, i) => ({
    week_start: `2026-09-${String(i * 7 + 1).padStart(2, '0')}`,
    hours: i === 7 ? 4 : i === 3 ? 2 : 0,
  }))
  render(<TrendChart weeks={weeks} />)
  const bars = screen.getAllByTestId('trend-bar')
  expect(bars).toHaveLength(8)
  expect(bars[7].style.height).toBe('100%')
  expect(bars[3].style.height).toBe('50%')
  expect(bars[0].style.height).toBe('0%')
})
