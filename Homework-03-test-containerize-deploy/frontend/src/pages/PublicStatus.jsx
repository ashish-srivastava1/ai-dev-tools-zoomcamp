import { useCallback, useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { lookupStatus, subscribeToQueue } from '../api/client';
import ServerSleepingNotice from '../components/ServerSleepingNotice';
import StatusBadge from '../components/StatusBadge';
import { formatMinutes, minutesSince } from '../lib/time';
import './PublicStatus.css';

const STATUS_COPY = {
  waiting: (party) =>
    party.position === 1
      ? "You're next! We'll call you shortly."
      : `${party.partiesAhead} ${party.partiesAhead === 1 ? 'party is' : 'parties are'} ahead of you.`,
  called: () => "You've been called — please check in with the host.",
  seated: () => 'Enjoy your meal!',
  removed: () => 'This party is no longer on the waitlist.',
};

export default function PublicStatus() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [code, setCode] = useState(searchParams.get('code') ?? '');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [party, setParty] = useState(null);
  const [notFound, setNotFound] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [serverDown, setServerDown] = useState(false);
  const [serverDownReason, setServerDownReason] = useState('gateway');
  // Live updates poll every few seconds; don't stack lookups while one is
  // still waiting on a sleeping server.
  const lookupInFlight = useRef(false);

  const runLookup = useCallback(async ({ code: c, phoneNumber: p }) => {
    if (!c && !p) return;
    if (lookupInFlight.current) return;
    lookupInFlight.current = true;
    setLoading(true);
    setError(null);
    try {
      const result = await lookupStatus({ code: c, phoneNumber: p });
      setParty(result);
      setNotFound(!result);
      setServerDown(false);
    } catch (err) {
      if (err.isServerUnavailable) {
        setServerDown(true);
        setServerDownReason(err.reason ?? 'gateway');
      } else {
        setServerDown(false);
        setError(err.message);
      }
    } finally {
      lookupInFlight.current = false;
      setLoading(false);
    }
  }, []);

  // Auto-lookup when arriving via a shared ?code=... link.
  useEffect(() => {
    const initialCode = searchParams.get('code');
    if (initialCode) {
      runLookup({ code: initialCode });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Keep the result live: re-run the last successful lookup whenever the
  // backend changes (host calls/seats/removes the party).
  useEffect(() => {
    if (!party) return undefined;
    return subscribeToQueue(() => {
      runLookup({ code: party.code });
    });
  }, [party, runLookup]);

  function handleSubmit(event) {
    event.preventDefault();
    if (code.trim()) {
      setSearchParams({ code: code.trim().toUpperCase() });
      runLookup({ code });
    } else {
      setSearchParams({});
      runLookup({ phoneNumber });
    }
  }

  return (
    <div className="public-status">
      {serverDown && <ServerSleepingNotice reason={serverDownReason} />}
      <section className="panel status-lookup-panel">
        <h2>Check your wait status</h2>
        <p className="status-help">Enter the short code you were given, or your phone number.</p>
        <form onSubmit={handleSubmit} className="status-lookup-form">
          <label>
            Queue code
            <input
              type="text"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="e.g. BEAN"
              maxLength={8}
            />
          </label>
          <div className="or-divider">or</div>
          <label>
            Phone number
            <input
              type="tel"
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              placeholder="555-010-1234"
            />
          </label>
          <button type="submit" className="primary-button" disabled={loading || (!code.trim() && !phoneNumber.trim())}>
            {loading ? 'Checking…' : 'Check status'}
          </button>
        </form>
        {error && <p className="form-error">{error}</p>}
      </section>

      {notFound && (
        <section className="panel">
          <p className="empty-state">
            We couldn't find a party with that code or phone number. Double-check with the host.
          </p>
        </section>
      )}

      {party && (
        <section className="panel status-result">
          <div className="status-result-header">
            <h2>{party.name}</h2>
            <StatusBadge status={party.status} />
          </div>
          <p className="status-message">{STATUS_COPY[party.status](party)}</p>

          {party.status === 'waiting' && (
            <div className="status-metrics">
              <div className="stat">
                <span className="stat-value">#{party.position}</span>
                <span className="stat-label">Your position</span>
              </div>
              <div className="stat">
                <span className="stat-value">{formatMinutes(party.estimatedWaitMinutes)}</span>
                <span className="stat-label">Estimated wait</span>
              </div>
              <div className="stat">
                <span className="stat-value">{formatMinutes(minutesSince(party.createdAt))}</span>
                <span className="stat-label">Waiting so far</span>
              </div>
            </div>
          )}

          <p className="status-footnote">
            Party of {party.partySize} · Code <code>{party.code}</code>
          </p>
        </section>
      )}
    </div>
  );
}
