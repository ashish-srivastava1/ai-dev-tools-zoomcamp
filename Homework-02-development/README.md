# TableTurn

A single-restaurant waitlist manager. Hosts add walk-in parties to a queue,
call them up when a table is ready, and remove them once seated or if they
leave. Customers can check their live queue position and estimated wait time
on a public status page — no account needed.

Built as Homework 2 for the [AI Dev Tools Zoomcamp](https://github.com/DataTalksClub/ai-dev-tools-zoomcamp),
using an AI coding assistant end-to-end: spec → frontend prototype (mocked
backend) → FastAPI backend → integration → SQLite persistence.

## Spec

See [`_docs/specs.md`](_docs/specs.md) for the full specification.

## Stack

- **Frontend:** React
- **Backend:** FastAPI (Python), managed with `uv`
- **Database:** SQLite via SQLAlchemy (mock store initially, swapped in later)
- **API contract:** OpenAPI (`openapi.yaml`)

## Running locally

### Frontend (mocked backend)

```
cd frontend
npm install
npm run dev
```

Opens at `http://localhost:5173`. All data is mocked in
[`frontend/src/api/mockBackend.js`](frontend/src/api/mockBackend.js) and
persisted to `localStorage`, so state survives a refresh and stays in sync
across tabs. Every backend call goes through
[`frontend/src/api/client.js`](frontend/src/api/client.js) — that's the one
file to change when the real backend is wired up.

Backend setup is still to be filled in — see `AGENTS.md` for the working
conventions used to build this.

## Status

- [x] Spec written
- [x] Frontend prototype (mocked backend)
- [ ] Backend (FastAPI, mock DB)
- [ ] Frontend/backend integration
- [ ] Real database (SQLite + SQLAlchemy)
