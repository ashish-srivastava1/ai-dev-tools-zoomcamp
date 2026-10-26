# LearnLoop — personal learning dashboard

Final project for the [AI Dev Tools Zoomcamp 2026](https://github.com/DataTalksClub/ai-dev-tools-zoomcamp).

## Problem

Working professionals who are upskilling, for example an engineering manager
doing an AI programme alongside a part-time course, learn in short sessions
spread over months. They use several sources (courses, books, side projects),
and it is hard to answer simple questions about their own progress:

- How many hours did I put in this week, and is that on target?
- Which track am I neglecting?
- How much of each course have I actually finished?
- Am I keeping a regular habit, or studying in bursts?

Spreadsheets and notes apps can store the raw data, but they don't turn it
into a quick progress view. So people lose momentum without noticing.

## What LearnLoop does

LearnLoop is a single-user web app for tracking learning:

1. **Tracks:** create learning tracks (e.g. "AI Dev Tools Zoomcamp",
   "IIM eMDP – Data Science & AI", "LLM agents"), each with a target in hours.
2. **Modules:** break each track into modules and mark them not started,
   in progress or done.
3. **Study sessions:** log a session with its date, duration, track, an
   optional module, and a short topic and notes.
4. **Dashboard:** see at a glance:
   - hours this week against your weekly goal
   - your current and longest study streak
   - hours per track against its target
   - module completion % per track
   - the last 8 weeks as a bar chart
   - recent sessions

**Expected behaviour:** a logged session shows up on the dashboard straight
away, the totals are correct, and data persists across restarts and
deploys. The full behaviour and acceptance criteria are in
[`product-spec.md`](product-spec.md).

## Status

🚧 Specification phase.

- **Task tracker:** [LearnLoop project board](https://github.com/users/ashish-srivastava1/projects/1) · [issues labelled `project-1`](https://github.com/ashish-srivastava1/ai-dev-tools-zoomcamp/issues?q=label%3Aproject-1)

## Repository guide

| Path | Purpose |
|---|---|
| `product-spec.md` | Product specification and acceptance criteria |
| `AGENTS.md` | Entry point for AI coding agents; links to the modular docs |
| `docs/` | Process, agent team, architecture, backlog |
| `frontend/` | React + Vite UI (to be built) |
| `backend/` | FastAPI + SQLAlchemy API (to be built) |
| `openapi.yaml` | API contract (to be written) |
| `docker-compose.yml` | Full local stack (to be added) |
| `ops/` | Observability, alerting, runbooks, on-call agent (to be added) |

Setup, run, test and deploy instructions will be added as each part lands.
