import { formatHours, shortWeek } from '../lib/format'

// 8-week bar chart (AC4.4) - plain CSS bars, no chart library.
export default function TrendChart({ weeks }) {
  const max = Math.max(1, ...weeks.map((w) => w.hours))
  return (
    <figure className="trend" aria-label="Hours per week, last 8 weeks">
      <div className="trend-bars">
        {weeks.map((w) => (
          <div className="trend-col" key={w.week_start}>
            <span className="trend-value">{w.hours ? formatHours(w.hours) : ''}</span>
            <div
              className="trend-bar"
              data-testid="trend-bar"
              title={`${shortWeek(w.week_start)}: ${formatHours(w.hours)}`}
              style={{ height: `${(w.hours / max) * 100}%` }}
            />
            <span className="trend-label">{shortWeek(w.week_start)}</span>
          </div>
        ))}
      </div>
    </figure>
  )
}
