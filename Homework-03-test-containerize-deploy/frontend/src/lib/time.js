export function minutesSince(iso) {
  return Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 60000));
}

export function formatMinutes(minutes) {
  if (minutes == null) return '—';
  if (minutes < 1) return '<1 min';
  return `${minutes} min`;
}
