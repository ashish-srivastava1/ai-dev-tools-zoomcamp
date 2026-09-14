# Specification: TableTurn — Restaurant Waitlist Manager

## 1. Overview

A single-restaurant waitlist manager. Hosts add walk-in parties to a queue,
call them up when a table is ready, and remove them once seated or if they
leave. Waiting customers can check their live queue position and estimated
wait time on a public status screen, without needing an account.

No table management, no multi-restaurant support, no login/auth — deliberately
kept simple for a one-week build.

## 2. Users

- **Host** — restaurant staff member. Uses the main dashboard to manage the
  queue. No login required (single shared host view for v1).
- **Customer** — no account. Given a shareable link or a queue number/code
  after being added, used to check their own status on a public page.

## 3. Core features

### 3.1 Host dashboard

- Add a party to the waitlist, capturing:
  - Name
  - Party size (number of people)
  - Phone number
  - Notes (free text — e.g. seating preference, allergy, "high chair needed")
- View the current queue, ordered by add time (FIFO), showing name, party
  size, wait time so far, and notes.
- "Call" a party (mark as called/notified) — moves them into a
  "called, waiting to seat" state, distinct from still-waiting.
- "Seat" a party — removes them from the active queue, marks as completed.
- "Remove" a party — for no-shows / customers who leave; removes from queue,
  marks as cancelled.
- See counts: parties waiting, parties called, average/typical wait so far
  today.

### 3.2 Public status screen

- A shareable link or simple lookup (e.g. by phone number or a short code
  given at signup) showing:
  - The customer's current position in the queue
  - Estimated wait time
  - Status: waiting / called / seated / removed
- Read-only. No ability to edit or cancel from this screen in v1.

### 3.3 Wait time estimation

- Simple estimate for v1: `(number of parties ahead in queue) × (average
  historical seating time)`, with a sane default average (e.g. 15 minutes)
  used until enough historical data exists.
- Not a hard commitment — framed as "estimated wait," consistent with how
  real waitlist apps hedge this.

## 4. Data model (initial)

**Party**
- id
- name
- party_size
- phone_number
- notes
- status: `waiting` | `called` | `seated` | `removed`
- created_at (queue join time)
- called_at (nullable)
- seated_at (nullable)
- removed_at (nullable)

No separate "restaurant" or "table" entities in v1 — single implicit
restaurant, no table tracking.

## 5. Out of scope (v1)

- Multiple restaurants / multi-tenant support
- Table management or table assignment
- Customer accounts / login
- SMS/notification sending (host manually calls/texts customers outside the
  app for now — the app just tracks status)
- Historical analytics/reporting beyond a simple average wait

## 6. Tech stack

- Frontend: React (or similar), served via Node.js tooling
- Backend: FastAPI (Python), managed with `uv`
- Database: mock/in-memory store initially, swapped for SQLite via
  SQLAlchemy later in the homework
- API contract: OpenAPI (`openapi.yaml`) as source of truth between frontend
  and backend

## 7. Success criteria for the homework demo

- Host can add a party with name/size/phone/notes and see it appear in the
  queue.
- Host can call and seat/remove parties; queue updates accordingly.
- Public status page reflects the same state (position, estimated wait,
  status) and stays consistent across a page refresh and across two
  browsers.
- Data persists in SQLite after a restart (not just in-memory).
