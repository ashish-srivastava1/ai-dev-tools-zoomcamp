# LearnLoop — Product Specification (v1)

## 1. Goal
Give one learner a reliable, at-a-glance view of how their learning is
going across several tracks, built from the study sessions they log.

## 2. User
A single learner (the owner of the deployment). There are no accounts or
roles. In the deployed demo, write operations can be protected with one
shared write token (see §6).

## 3. Concepts
| Entity | Fields |
|---|---|
| **Track** | id, name (unique, 1–80 chars), description (optional), target_hours (>0), color (hex `#RRGGBB`), archived (bool), created_at |
| **Module** | id, track_id, title (1–120 chars), position (int), status: `not_started` / `in_progress` / `done` |
| **Session** | id, track_id, module_id (optional; must belong to the track), date (local date, not in the future), minutes (1–600), topic (1–120 chars), notes (optional, ≤2000 chars), created_at |
| **Settings** | weekly_goal_hours (default 5), timezone (IANA, default `Asia/Kolkata`), week_start (`monday` or `sunday`, default `monday`) |

## 4. Features and acceptance criteria

### F1 — Manage tracks
- AC1.1: I can create a track with a name and target hours; it appears in the track list.
- AC1.2: A duplicate name (case-insensitive) or target ≤ 0 is rejected with a clear message (HTTP 422).
- AC1.3: I can edit a track's name, description, target and colour.
- AC1.4: I can archive a track. Archived tracks are hidden from the dashboard and the session form, but their sessions are kept.

### F2 — Manage modules
- AC2.1: I can add modules to a track. They are listed in `position` order.
- AC2.2: I can change a module's status. Track completion % = done modules ÷ all modules, rounded to the nearest whole number; 0 % when there are no modules.
- AC2.3: I can reorder modules and delete a module. Deleting a module keeps its sessions, with module_id set to null.

### F3 — Log study sessions (key user journey)
- AC3.1: I can log a session with date, minutes, track, an optional module, topic and notes. After saving, the dashboard reflects it without a manual refresh.
- AC3.2: Validation: minutes 1–600, date not in the future (in the user's timezone), the track exists and is not archived, and the module belongs to the track. Invalid input returns 422 and the form shows the error.
- AC3.3: I can edit or delete a session, and the dashboard totals update to match.
- AC3.4: I can list sessions filtered by track and by date range, newest first, paginated (20 per page).

### F4 — Dashboard
- AC4.1: **This week:** total hours from week_start up to today in the user's timezone, against weekly_goal_hours, as a % and a progress bar.
- AC4.2: **Streak:** the current streak counts consecutive calendar days, ending today or yesterday, with at least one session. The longest streak is the longest such run ever. Both use the user's timezone and must be correct across month and year boundaries.
- AC4.3: **Per-track:** hours logged against target_hours, and module completion %.
- AC4.4: **Trend:** hours per week for the last 8 weeks, including weeks with 0.
- AC4.5: **Recent:** the 5 most recent sessions.
- AC4.6: With no data, the dashboard shows an empty state that prompts me to create a track.

### F5 — Settings
- AC5.1: I can change the weekly goal, timezone and week start. The dashboard recalculates using them.

## 5. Out of scope (v1)
Multiple users or login, AI features, reminders or notifications, importing from other tools, mobile apps.

## 6. Non-functional requirements
- **Persistence:** PostgreSQL. All data survives restarts and redeploys.
- **One-command run:** `docker compose up` starts the database, the app and the observability stack.
- **Security:** if `WRITE_TOKEN` is set, every POST/PUT/PATCH/DELETE request needs `Authorization: Bearer <token>`. Secrets are never committed.
- **Performance and reliability (SLO for the key journey: log a session and load the dashboard):** 99 % of requests succeed (non-5xx) and p95 latency stays under 500 ms, both measured over 30 days.
- **Observability:** the key journey emits metrics, traces and structured JSON logs that share a trace_id. Session topics, notes and the write token never go to telemetry.
- **Testing:** unit tests for the backend and frontend, plus integration tests against a real Postgres, all run with one command.

## 7. Key user journey (instrumented and alerted)
Open the dashboard → log a session → the dashboard reloads with updated totals.
Alerts fire on **user impact** for this journey: the 5xx rate on `POST /api/sessions` or `GET /api/dashboard` goes above 5 % over 5 minutes, or p95 latency goes above 1 s. They do not fire on CPU or memory.
