# TableTurn

A single-restaurant waitlist manager. Hosts add walk-in parties to a queue,
call them up when a table is ready, and remove them once seated or if they
leave. Customers can check their live queue position and estimated wait time
on a public status page — no account needed.

Originally built as Homework 2 for the [AI Dev Tools Zoomcamp](https://github.com/DataTalksClub/ai-dev-tools-zoomcamp)
(spec → frontend prototype (mocked backend) → FastAPI backend → integration →
SQLite persistence). This folder is a fresh copy used for **Homework 3:
"Test, Containerize, and Deploy an AI-Assisted App."** The goal here is to
containerize the app, move from SQLite to Postgres, add integration/end-to-end
tests, wire up CI/CD, and deploy again — the earlier Render + Vercel
deployment details from Homework 2 were intentionally stripped out of this
copy so it can be redeployed fresh as part of this module.

## Spec

See [`_docs/specs.md`](_docs/specs.md) for the full specification.

## Stack

- **Frontend:** React
- **Backend:** FastAPI (Python), managed with `uv`
- **Database:** SQLite via SQLAlchemy (moving to Postgres as part of this module)
- **API contract:** OpenAPI (`openapi.yaml`)

## Running locally

Run both together — the frontend calls the backend directly over HTTP, so
neither is useful alone.

### Backend

```
uv run --project backend uvicorn backend.main:app --reload --port 8000
```

Opens the API at `http://localhost:8000` (interactive docs at `/docs`).
Data is persisted to a SQLite file at `backend/tableturn.db` (created
automatically on first run) via SQLAlchemy
([`backend/src/backend/store.py`](backend/src/backend/store.py)), behind
the same [`openapi.yaml`](openapi.yaml) contract as before — swapping the
mock store for a real database didn't change the API. Delete the file to
reset all data.

Run the test suite:

```
uv run --project backend pytest
```

### Frontend

```
cd frontend
npm install
npm run dev
```

Opens at `http://localhost:5173` and talks to the backend at
`http://localhost:8000` by default (override with `VITE_API_BASE_URL`, see
`frontend/.env.example`). Every backend call goes through
[`frontend/src/api/client.js`](frontend/src/api/client.js) — that was the
only file touched to swap the mock for the real API.

If the frontend can't reach the backend, it now says why: a genuine timeout
or a gateway error (502/503/504) shows the "server is asleep — free-tier
cold start" message, while any other failure — most commonly, just not
having started the backend locally — shows a plain "can't reach the
backend, is it running?" message instead. See the `reason` handling in
[`frontend/src/api/client.js`](frontend/src/api/client.js).

## Status

Inherited from Homework 2:

- [x] Spec written
- [x] Frontend prototype (mocked backend)
- [x] Backend (FastAPI, mock DB)
- [x] Frontend/backend integration
- [x] Real database (SQLite + SQLAlchemy)

Homework 3 (this folder):

- [ ] Containerize (`Dockerfile` + `docker-compose.yml`)
- [ ] Migrate SQLite → Postgres
- [ ] Integration tests (`tests/integration/`)
- [ ] End-to-end tests (Playwright)
- [ ] CI workflow (lint, unit, integration, build) — `.github/workflows/ci.yml`
- [ ] CD workflow (deploy on main after tests pass) — `.github/workflows/deploy.yml`
- [ ] Deploy to Render with a managed Postgres database
- [ ] `docs/testing.md`, `docs/deployment.md`, `docs/release-process.md`

## TableTurn Demo

https://github.com/user-attachments/assets/0a2dc6f9-7216-4ea1-9766-30b93253e1f6
