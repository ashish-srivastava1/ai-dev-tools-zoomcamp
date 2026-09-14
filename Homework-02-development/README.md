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

_To be filled in once the frontend and backend exist — see `AGENTS.md` for
the working conventions used to build this._

## Status

- [x] Spec written
- [ ] Frontend prototype (mocked backend)
- [ ] Backend (FastAPI, mock DB)
- [ ] Frontend/backend integration
- [ ] Real database (SQLite + SQLAlchemy)
