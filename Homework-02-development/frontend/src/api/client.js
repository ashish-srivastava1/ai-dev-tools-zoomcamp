// Single entry point for every backend call the app makes.
//
// For now this wraps a localStorage-backed mock (`./mockBackend.js`) that
// simulates network latency. When the FastAPI backend exists, swap the
// bodies of these functions for `fetch()` calls against the real API —
// nothing outside this file needs to change.

import * as mock from './mockBackend';

const [MIN_LATENCY_MS, MAX_LATENCY_MS] = [150, 400];

function networkDelay() {
  const ms = MIN_LATENCY_MS + Math.random() * (MAX_LATENCY_MS - MIN_LATENCY_MS);
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/** Full queue (all statuses), FIFO by join time, with position/wait estimate attached. */
export async function listQueue() {
  await networkDelay();
  return mock.listQueue();
}

/** Dashboard counters: parties waiting, called, and today's average wait. */
export async function getStats() {
  await networkDelay();
  return mock.getStats();
}

/** Adds a party to the waitlist. Throws on invalid input. */
export async function addParty(input) {
  await networkDelay();
  return mock.addParty(input);
}

/** Marks a waiting party as called. */
export async function callParty(id) {
  await networkDelay();
  return mock.callParty(id);
}

/** Marks a waiting/called party as seated (completes them). */
export async function seatParty(id) {
  await networkDelay();
  return mock.seatParty(id);
}

/** Marks a waiting/called party as removed (no-show / left). */
export async function removeParty(id) {
  await networkDelay();
  return mock.removeParty(id);
}

/** Public lookup by short code or phone number. Returns null if no match. */
export async function lookupStatus(query) {
  await networkDelay();
  return mock.lookupStatus(query);
}

/**
 * Subscribes to queue changes (including edits made in other tabs).
 * Returns an unsubscribe function. No network delay — this is local wiring,
 * not a request.
 */
export function subscribeToQueue(callback) {
  return mock.subscribe(callback);
}
