import { useEffect, useState } from 'react';
import { addParty, callParty, removeParty, seatParty } from '../api/client';
import ServerSleepingNotice from '../components/ServerSleepingNotice';
import StatusBadge from '../components/StatusBadge';
import { useLiveQueue } from '../hooks/useLiveQueue';
import { formatMinutes, minutesSince } from '../lib/time';
import './HostDashboard.css';

const EMPTY_FORM = { name: '', partySize: '2', phoneNumber: '', notes: '' };

export default function HostDashboard() {
  const { queue, stats, loading, serverDown: pollingServerDown, refresh } = useLiveQueue();
  const [form, setForm] = useState(EMPTY_FORM);
  const [formError, setFormError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [lastAdded, setLastAdded] = useState(null);
  const [pendingId, setPendingId] = useState(null);
  const [actionError, setActionError] = useState(null);
  const [actionServerDown, setActionServerDown] = useState(false);
  const serverDown = pollingServerDown || actionServerDown;
  const [, forceTick] = useState(0);

  // Re-render periodically so "wait so far" keeps ticking up.
  useEffect(() => {
    const interval = setInterval(() => forceTick((t) => t + 1), 30000);
    return () => clearInterval(interval);
  }, []);

  const activeParties = queue.filter((p) => p.status === 'waiting' || p.status === 'called');
  const finishedParties = queue.filter((p) => p.status === 'seated' || p.status === 'removed');

  async function handleAddParty(event) {
    event.preventDefault();
    setFormError(null);
    setActionServerDown(false);
    setSubmitting(true);
    try {
      const created = await addParty({
        name: form.name,
        partySize: form.partySize,
        phoneNumber: form.phoneNumber,
        notes: form.notes,
      });
      setForm(EMPTY_FORM);
      setLastAdded(created);
      await refresh();
    } catch (err) {
      if (err.isServerUnavailable) setActionServerDown(true);
      else setFormError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleAction(action, id) {
    setActionError(null);
    setActionServerDown(false);
    setPendingId(id);
    try {
      if (action === 'call') await callParty(id);
      if (action === 'seat') await seatParty(id);
      if (action === 'remove') await removeParty(id);
      await refresh();
    } catch (err) {
      if (err.isServerUnavailable) setActionServerDown(true);
      else setActionError(err.message);
    } finally {
      setPendingId(null);
    }
  }

  return (
    <div className="dashboard">
      {serverDown && <ServerSleepingNotice />}
      <section className="panel add-party-panel">
        <h2>Add a party</h2>
        <form onSubmit={handleAddParty} className="add-party-form">
          <label>
            Name
            <input
              type="text"
              required
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="Alvarez"
            />
          </label>
          <label>
            Party size
            <input
              type="number"
              min="1"
              required
              value={form.partySize}
              onChange={(e) => setForm({ ...form, partySize: e.target.value })}
            />
          </label>
          <label>
            Phone number
            <input
              type="tel"
              required
              value={form.phoneNumber}
              onChange={(e) => setForm({ ...form, phoneNumber: e.target.value })}
              placeholder="555-010-1234"
            />
          </label>
          <label className="notes-field">
            Notes
            <textarea
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
              placeholder="Seating preference, allergy, high chair needed…"
              rows={2}
            />
          </label>
          {formError && <p className="form-error">{formError}</p>}
          <button type="submit" className="primary-button" disabled={submitting}>
            {submitting ? 'Adding…' : 'Add to waitlist'}
          </button>
        </form>

        {lastAdded && (
          <div className="last-added">
            <p>
              Added <strong>{lastAdded.name}</strong> — share this with them:
            </p>
            <p className="last-added-code">
              Code <code>{lastAdded.code}</code>
            </p>
            <p className="last-added-link">
              <a href={`/status?code=${lastAdded.code}`} target="_blank" rel="noreferrer">
                {window.location.origin}/status?code={lastAdded.code}
              </a>
            </p>
          </div>
        )}
      </section>

      <section className="panel">
        <div className="stats-row">
          <div className="stat">
            <span className="stat-value">{stats.waitingCount}</span>
            <span className="stat-label">Waiting</span>
          </div>
          <div className="stat">
            <span className="stat-value">{stats.calledCount}</span>
            <span className="stat-label">Called</span>
          </div>
          <div className="stat">
            <span className="stat-value">{formatMinutes(stats.avgWaitTodayMinutes)}</span>
            <span className="stat-label">Avg wait today</span>
          </div>
        </div>

        {actionError && <p className="form-error">{actionError}</p>}

        <h2>Current queue</h2>
        {loading ? (
          <p className="empty-state">
            {serverDown ? 'The queue will appear once the server is back.' : 'Loading queue…'}
          </p>
        ) : activeParties.length === 0 ? (
          <p className="empty-state">No one is waiting right now.</p>
        ) : (
          <div className="table-wrap">
            <table className="queue-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Name</th>
                  <th>Size</th>
                  <th>Waiting</th>
                  <th>Notes</th>
                  <th>Status</th>
                  <th aria-label="Actions" />
                </tr>
              </thead>
              <tbody>
                {activeParties.map((party) => (
                  <tr key={party.id}>
                    <td>{party.position ?? '—'}</td>
                    <td>
                      <div className="party-name">{party.name}</div>
                      <div className="party-phone">{party.phoneNumber}</div>
                    </td>
                    <td>{party.partySize}</td>
                    <td>{formatMinutes(minutesSince(party.createdAt))}</td>
                    <td className="party-notes">{party.notes || '—'}</td>
                    <td>
                      <StatusBadge status={party.status} />
                    </td>
                    <td className="party-actions">
                      {party.status === 'waiting' && (
                        <button
                          className="secondary-button"
                          disabled={pendingId === party.id}
                          onClick={() => handleAction('call', party.id)}
                        >
                          Call
                        </button>
                      )}
                      <button
                        className="secondary-button"
                        disabled={pendingId === party.id}
                        onClick={() => handleAction('seat', party.id)}
                      >
                        Seat
                      </button>
                      <button
                        className="danger-button"
                        disabled={pendingId === party.id}
                        onClick={() => handleAction('remove', party.id)}
                      >
                        Remove
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {finishedParties.length > 0 && (
          <details className="history">
            <summary>Today's completed &amp; removed ({finishedParties.length})</summary>
            <div className="table-wrap">
              <table className="queue-table queue-table--compact">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Size</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {finishedParties.map((party) => (
                    <tr key={party.id}>
                      <td>{party.name}</td>
                      <td>{party.partySize}</td>
                      <td>
                        <StatusBadge status={party.status} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
        )}
      </section>
    </div>
  );
}
