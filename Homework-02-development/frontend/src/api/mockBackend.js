// In-memory + localStorage-backed mock of the future FastAPI backend.
// Not imported directly by any page/component — everything goes through
// `../api/client.js`, so this file can be deleted wholesale once the real
// backend exists.

const STORAGE_KEY = 'tableturn.parties';
const DEFAULT_AVG_SEATING_MINUTES = 15;

const listeners = new Set();

function nowIso() {
  return new Date().toISOString();
}

function generateId() {
  return `p_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}

function generateCode(existing) {
  const alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'; // no 0/O/1/I
  let code;
  do {
    code = Array.from({ length: 4 }, () => alphabet[Math.floor(Math.random() * alphabet.length)]).join('');
  } while (existing.some((p) => p.code === code));
  return code;
}

function seedData() {
  const now = Date.now();
  const minutesAgo = (m) => new Date(now - m * 60 * 1000).toISOString();
  const seed = [
    {
      id: generateId(),
      code: 'BEAN',
      name: 'Alvarez',
      partySize: 4,
      phoneNumber: '555-010-1234',
      notes: 'Window seat if possible',
      status: 'waiting',
      createdAt: minutesAgo(22),
      calledAt: null,
      seatedAt: null,
      removedAt: null,
    },
    {
      id: generateId(),
      code: 'KIWI',
      name: 'Nguyen',
      partySize: 2,
      phoneNumber: '555-010-5678',
      notes: '',
      status: 'waiting',
      createdAt: minutesAgo(14),
      calledAt: null,
      seatedAt: null,
      removedAt: null,
    },
    {
      id: generateId(),
      code: 'PLUM',
      name: 'Osei',
      partySize: 3,
      phoneNumber: '555-010-9012',
      notes: 'High chair needed',
      status: 'called',
      createdAt: minutesAgo(28),
      calledAt: minutesAgo(3),
      seatedAt: null,
      removedAt: null,
    },
    {
      id: generateId(),
      code: 'FERN',
      name: 'Delgado',
      partySize: 5,
      phoneNumber: '555-010-3456',
      notes: 'Allergy: peanuts',
      status: 'seated',
      createdAt: minutesAgo(55),
      calledAt: minutesAgo(40),
      seatedAt: minutesAgo(38),
      removedAt: null,
    },
  ];
  return seed;
}

function load() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      const seeded = seedData();
      save(seeded);
      return seeded;
    }
    return JSON.parse(raw);
  } catch {
    return seedData();
  }
}

function save(parties) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(parties));
}

let parties = load();

// Cross-tab sync: another tab/window writing to the same key notifies us.
window.addEventListener('storage', (event) => {
  if (event.key === STORAGE_KEY) {
    parties = load();
    notify();
  }
});

function notify() {
  for (const listener of listeners) listener();
}

function persist(next) {
  parties = next;
  save(parties);
  notify();
}

export function subscribe(callback) {
  listeners.add(callback);
  return () => listeners.delete(callback);
}

function minutesBetween(startIso, endIso) {
  return (new Date(endIso).getTime() - new Date(startIso).getTime()) / 60000;
}

function averageSeatingMinutes() {
  const completed = parties.filter((p) => p.status === 'seated' && p.seatedAt);
  if (completed.length === 0) return DEFAULT_AVG_SEATING_MINUTES;
  const total = completed.reduce((sum, p) => sum + minutesBetween(p.createdAt, p.seatedAt), 0);
  return total / completed.length;
}

function isToday(iso) {
  if (!iso) return false;
  const d = new Date(iso);
  const now = new Date();
  return (
    d.getFullYear() === now.getFullYear() &&
    d.getMonth() === now.getMonth() &&
    d.getDate() === now.getDate()
  );
}

// Attaches derived fields (queue position, estimated wait) without mutating
// the stored record.
function withDerived(all) {
  const avg = averageSeatingMinutes();
  const waitingInOrder = all
    .filter((p) => p.status === 'waiting')
    .sort((a, b) => new Date(a.createdAt) - new Date(b.createdAt));

  return all.map((p) => {
    if (p.status === 'waiting') {
      const position = waitingInOrder.findIndex((w) => w.id === p.id) + 1;
      const partiesAhead = position - 1;
      return {
        ...p,
        position,
        partiesAhead,
        estimatedWaitMinutes: Math.round(partiesAhead * avg),
      };
    }
    if (p.status === 'called') {
      return { ...p, position: null, partiesAhead: 0, estimatedWaitMinutes: 0 };
    }
    return { ...p, position: null, partiesAhead: null, estimatedWaitMinutes: null };
  });
}

export function listQueue() {
  const all = withDerived(parties).sort((a, b) => new Date(a.createdAt) - new Date(b.createdAt));
  return all;
}

export function getStats() {
  const waitingCount = parties.filter((p) => p.status === 'waiting').length;
  const calledCount = parties.filter((p) => p.status === 'called').length;
  const seatedToday = parties.filter((p) => p.status === 'seated' && isToday(p.seatedAt));
  const avgWaitTodayMinutes =
    seatedToday.length > 0
      ? Math.round(
          seatedToday.reduce((sum, p) => sum + minutesBetween(p.createdAt, p.seatedAt), 0) /
            seatedToday.length
        )
      : null;
  return { waitingCount, calledCount, avgWaitTodayMinutes };
}

export function addParty({ name, partySize, phoneNumber, notes }) {
  const trimmedName = (name ?? '').trim();
  const trimmedPhone = (phoneNumber ?? '').trim();
  const size = Number(partySize);

  if (!trimmedName) throw new Error('Name is required.');
  if (!trimmedPhone) throw new Error('Phone number is required.');
  if (!Number.isFinite(size) || size < 1) throw new Error('Party size must be at least 1.');

  const party = {
    id: generateId(),
    code: generateCode(parties),
    name: trimmedName,
    partySize: size,
    phoneNumber: trimmedPhone,
    notes: (notes ?? '').trim(),
    status: 'waiting',
    createdAt: nowIso(),
    calledAt: null,
    seatedAt: null,
    removedAt: null,
  };

  persist([...parties, party]);
  return withDerived(parties).find((p) => p.id === party.id);
}

function updateStatus(id, patch) {
  const idx = parties.findIndex((p) => p.id === id);
  if (idx === -1) throw new Error('Party not found.');
  const next = parties.slice();
  next[idx] = { ...next[idx], ...patch };
  persist(next);
  return withDerived(parties).find((p) => p.id === id);
}

export function callParty(id) {
  const party = parties.find((p) => p.id === id);
  if (!party) throw new Error('Party not found.');
  if (party.status !== 'waiting') throw new Error('Only waiting parties can be called.');
  return updateStatus(id, { status: 'called', calledAt: nowIso() });
}

export function seatParty(id) {
  const party = parties.find((p) => p.id === id);
  if (!party) throw new Error('Party not found.');
  if (party.status !== 'waiting' && party.status !== 'called') {
    throw new Error('Only waiting or called parties can be seated.');
  }
  return updateStatus(id, { status: 'seated', seatedAt: nowIso() });
}

export function removeParty(id) {
  const party = parties.find((p) => p.id === id);
  if (!party) throw new Error('Party not found.');
  if (party.status !== 'waiting' && party.status !== 'called') {
    throw new Error('Only waiting or called parties can be removed.');
  }
  return updateStatus(id, { status: 'removed', removedAt: nowIso() });
}

export function lookupStatus({ code, phoneNumber }) {
  const normalizedCode = (code ?? '').trim().toUpperCase();
  const normalizedPhone = (phoneNumber ?? '').trim();

  const all = withDerived(parties);
  let match = null;

  if (normalizedCode) {
    match = all.find((p) => p.code === normalizedCode) ?? null;
  } else if (normalizedPhone) {
    const candidates = all
      .filter((p) => p.phoneNumber === normalizedPhone)
      .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
    match = candidates[0] ?? null;
  }

  return match;
}
