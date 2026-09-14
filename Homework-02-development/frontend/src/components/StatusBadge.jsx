const LABELS = {
  waiting: 'Waiting',
  called: 'Called',
  seated: 'Seated',
  removed: 'Removed',
};

export default function StatusBadge({ status }) {
  return <span className={`status-badge status-badge--${status}`}>{LABELS[status] ?? status}</span>;
}
