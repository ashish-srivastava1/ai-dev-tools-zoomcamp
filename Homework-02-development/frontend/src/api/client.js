// Single entry point for every backend call the app makes.
//
// Talks to the real FastAPI backend (see ../../../backend and
// ../../../openapi.yaml). Two things happen here that the rest of the app
// doesn't need to know about:
//  - field names are translated between the API's snake_case and the
//    camelCase every page already uses (unchanged from the mocked version)
//  - queue changes are polled rather than pushed, since the backend has no
//    websocket/SSE channel yet; `subscribeToQueue` hides that behind the
//    same callback-based API the mock used for its storage-event pub/sub

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';
const POLL_INTERVAL_MS = 4000;

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    });
  } catch {
    throw new Error('Could not reach the server. Is the backend running?');
  }

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const error = new Error(extractErrorMessage(body) ?? `Request failed (${response.status}).`);
    error.status = response.status;
    throw error;
  }

  if (response.status === 204) return null;
  return response.json();
}

// FastAPI returns `{ detail: "..." }` for our own HTTPExceptions, but
// `{ detail: [{ msg, loc, type }, ...] }` for pydantic validation errors.
function extractErrorMessage(body) {
  if (!body?.detail) return null;
  if (typeof body.detail === 'string') return body.detail;
  if (Array.isArray(body.detail)) {
    return body.detail.map((e) => (e.msg ?? '').replace(/^Value error,\s*/, '')).join(' ');
  }
  return null;
}

function toApiPartyPayload({ name, partySize, phoneNumber, notes }) {
  return {
    name,
    party_size: Number(partySize),
    phone_number: phoneNumber,
    notes: notes ?? '',
  };
}

function fromApiParty(party) {
  if (!party) return null;
  return {
    id: party.id,
    code: party.code,
    name: party.name,
    partySize: party.party_size,
    phoneNumber: party.phone_number,
    notes: party.notes,
    status: party.status,
    createdAt: party.created_at,
    calledAt: party.called_at,
    seatedAt: party.seated_at,
    removedAt: party.removed_at,
    position: party.position,
    partiesAhead: party.parties_ahead,
    estimatedWaitMinutes: party.estimated_wait_minutes,
  };
}

function fromApiStats(stats) {
  return {
    waitingCount: stats.waiting_count,
    calledCount: stats.called_count,
    avgWaitTodayMinutes: stats.avg_wait_today_minutes,
  };
}

/** Full queue (all statuses), FIFO by join time, with position/wait estimate attached. */
export async function listQueue() {
  const parties = await request('/api/parties');
  return parties.map(fromApiParty);
}

/** Dashboard counters: parties waiting, called, and today's average wait. */
export async function getStats() {
  const stats = await request('/api/stats');
  return fromApiStats(stats);
}

/** Adds a party to the waitlist. Throws on invalid input. */
export async function addParty(input) {
  const party = await request('/api/parties', {
    method: 'POST',
    body: JSON.stringify(toApiPartyPayload(input)),
  });
  notifySubscribers();
  return fromApiParty(party);
}

/** Marks a waiting party as called. */
export async function callParty(id) {
  const party = await request(`/api/parties/${id}/call`, { method: 'POST' });
  notifySubscribers();
  return fromApiParty(party);
}

/** Marks a waiting/called party as seated (completes them). */
export async function seatParty(id) {
  const party = await request(`/api/parties/${id}/seat`, { method: 'POST' });
  notifySubscribers();
  return fromApiParty(party);
}

/** Marks a waiting/called party as removed (no-show / left). */
export async function removeParty(id) {
  const party = await request(`/api/parties/${id}/remove`, { method: 'POST' });
  notifySubscribers();
  return fromApiParty(party);
}

/** Public lookup by short code or phone number. Returns null if no match. */
export async function lookupStatus({ code, phoneNumber }) {
  const params = new URLSearchParams();
  if (code) params.set('code', code);
  else if (phoneNumber) params.set('phone_number', phoneNumber);

  try {
    const party = await request(`/api/status?${params.toString()}`);
    return fromApiParty(party);
  } catch (err) {
    if (err.status === 404) return null;
    throw err;
  }
}

const subscribers = new Set();
let pollHandle = null;

function notifySubscribers() {
  for (const callback of subscribers) callback();
}

/**
 * Subscribes to queue changes. Fires immediately after any mutation made
 * from this tab, and on a fixed poll interval otherwise (to pick up changes
 * from the host dashboard or another tab). Returns an unsubscribe function.
 */
export function subscribeToQueue(callback) {
  subscribers.add(callback);
  if (!pollHandle) {
    pollHandle = setInterval(notifySubscribers, POLL_INTERVAL_MS);
  }
  return () => {
    subscribers.delete(callback);
    if (subscribers.size === 0 && pollHandle) {
      clearInterval(pollHandle);
      pollHandle = null;
    }
  };
}
