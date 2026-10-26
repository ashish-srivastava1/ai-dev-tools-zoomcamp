import { describe, expect, it } from 'vitest'
import { clampPercent, formatDate, formatHours, formatMinutes, shortWeek, todayIn } from './format'

describe('format helpers', () => {
  it('formatHours', () => {
    expect(formatHours(0)).toBe('0 h')
    expect(formatHours(0.5)).toBe('30 min')
    expect(formatHours(2)).toBe('2 h')
    expect(formatHours(2.25)).toBe('2.3 h')
  })

  it('formatMinutes', () => {
    expect(formatMinutes(45)).toBe('45 min')
    expect(formatMinutes(60)).toBe('1 h')
    expect(formatMinutes(95)).toBe('1 h 35 min')
  })

  it('formatDate and shortWeek do not shift days across timezones', () => {
    expect(formatDate('2026-10-21')).toContain('21')
    expect(formatDate('2026-10-21')).toContain('2026')
    expect(shortWeek('2027-01-01')).toContain('1')
    expect(formatDate('')).toBe('')
  })

  it('todayIn respects the timezone', () => {
    const now = new Date('2026-12-31T20:00:00Z')
    expect(todayIn('Asia/Kolkata', now)).toBe('2027-01-01')
    expect(todayIn('America/New_York', now)).toBe('2026-12-31')
  })

  it('clampPercent', () => {
    expect(clampPercent(150)).toBe(100)
    expect(clampPercent(-3)).toBe(0)
    expect(clampPercent('x')).toBe(0)
  })
})
