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
- **Database:** SQLAlchemy — SQLite for local dev, Postgres in containers/deploy (swap via `DATABASE_URL`)
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

## Running with Docker

The whole app — frontend **and** backend — runs from a single container. A
multi-stage [`Dockerfile`](Dockerfile) builds the React frontend with Node,
then copies the static bundle into a Python image where the FastAPI backend
serves both the API (`/api/...`, `/health`) and the SPA (everything else) on
one origin. Because they share an origin, the frontend calls the API with
relative URLs — no `VITE_API_BASE_URL` or CORS needed.

[`docker-compose.yml`](docker-compose.yml) runs **two services** — a
Postgres database and the app — which is the production-style setup: local
`uv run` dev uses SQLite (zero setup), while containers use Postgres. The
backend is database-agnostic (SQLAlchemy + a portable `UTCDateTime` column
type), so the switch is just the `DATABASE_URL` env var — no model or query
changes. Postgres runs the [psycopg 3](https://www.psycopg.org/psycopg3/)
driver.

With [Docker](https://www.docker.com/products/docker-desktop/) installed and
running:

```
docker compose up --build
```

Open `http://localhost:8000` for the app (API docs at `/docs`). Compose
health-checks Postgres and holds the app back (`depends_on: service_healthy`)
until the database is ready to accept connections. Postgres data is persisted
in a named volume (`pgdata`), so it survives restarts. Stop with `Ctrl+C`, or
`docker compose down` (add `-v` to also wipe the database volume).

Prefer plain Docker without Postgres? The image still runs standalone on
SQLite — handy for a quick smoke test:

```
docker build -t tableturn .
docker run --rm -p 8000:8000 tableturn
```

To point at any other database (a managed Postgres in deployment, for
example), set `DATABASE_URL` — e.g.
`postgresql+psycopg://user:pass@host:5432/dbname`.

## Status

Inherited from Homework 2:

- [x] Spec written
- [x] Frontend prototype (mocked backend)
- [x] Backend (FastAPI, mock DB)
- [x] Frontend/backend integration
- [x] Real database (SQLite + SQLAlchemy)

Homework 3 (this folder):

- [x] Containerize (`Dockerfile` + `docker-compose.yml`)
- [x] Migrate SQLite → Postgres
- [ ] Integration tests (`tests/integration/`)
- [ ] End-to-end tests (Playwright)
- [ ] CI workflow (lint, unit, integration, build) — `.github/workflows/ci.yml`
- [ ] CD workflow (deploy on main after tests pass) — `.github/workflows/deploy.yml`
- [ ] Deploy to Render with a managed Postgres database
- [ ] `docs/testing.md`, `docs/deployment.md`, `docs/release-process.md`

## TableTurn Demo

https://github.com/user-attachments/assets/0a2dc6f9-7216-4ea1-9766-30b93253e1f6
