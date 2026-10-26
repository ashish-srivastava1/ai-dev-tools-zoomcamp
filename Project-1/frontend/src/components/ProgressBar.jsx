import { clampPercent } from '../lib/format'

export default function ProgressBar({ percent, color, label }) {
  const width = clampPercent(percent)
  return (
    <div
      className="progress"
      role="progressbar"
      aria-label={label}
      aria-valuenow={Number(percent) || 0}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <div className="progress-fill" style={{ width: `${width}%`, background: color }} />
    </div>
  )
}
