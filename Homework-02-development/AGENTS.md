# AGENTS.md

Instructions for AI coding assistants working in this repository.

## Project

TableTurn — a single-restaurant waitlist manager. Full spec lives in
`_docs/specs.md`. Read it before making changes that touch scope or
behavior.

## Structure

- `_docs/specs.md` — source of truth for what the app should do
- `frontend/` — React frontend
- `backend/` — FastAPI backend, managed with `uv`
- `openapi.yaml` — API contract shared between frontend and backend

## Working conventions

- Treat `_docs/specs.md` as the source of truth. If a request conflicts with
  it, flag the conflict rather than silently deviating.
- Backend: use `uv` for all Python package management (`uv add`, `uv run`,
  etc.) — do not use bare `pip`.
- Backend: write tests before implementing endpoints, per the homework
  workflow. Keep tests passing after any change.
- Database: keep the app database-agnostic via SQLAlchemy — avoid
  database-specific SQL or features that would break a swap away from
  SQLite.
- Frontend: centralize backend calls in one place (a single API client
  module) so mocking and later real-backend wiring stay a one-file change.
- Keep the mock backend/mock store clearly separated from real
  implementations so swapping one for the other doesn't require touching
  unrelated code.
- Don't introduce multi-restaurant, table-management, or auth/login
  features — explicitly out of scope for v1 per the spec.

## Commands

Frontend:

```
cd frontend
npm install
npm run dev      # dev server at http://localhost:5173
npm run build    # production build
npm run lint     # oxlint
```

Backend:

```
uv run --project backend uvicorn backend.main:app --reload --port 8000  # dev server at http://localhost:8000 (docs at /docs)
uv run --project backend pytest                                        # test suite
uv add --project backend <package>                                     # add a runtime dependency
uv add --project backend --dev <package>                               # add a dev dependency
```

## Frontend notes

- Scaffolded with Vite (`react` template) + `react-router-dom`.
- `src/api/client.js` is the single module every page/component calls for
  data. It now calls the real FastAPI backend (`VITE_API_BASE_URL`, default
  `http://localhost:8000`) — this is the only file that changed when the mock
  was swapped out; no page/component was touched. It also translates
  snake_case API fields to the camelCase every page uses, and turns
  `{ detail }` error responses into `Error` messages.
- Queue updates are polled every 4s (plus an immediate refresh after any
  mutation made from the same tab) via `subscribeToQueue`, since the backend
  has no websocket/SSE channel — the localStorage-driven instant cross-tab
  sync from the mocked version is gone now that state lives server-side.
- Routes: `/` is the host dashboard, `/status` is the public, read-only
  status lookup (by short code or phone number).
- Run both `npm run dev` (frontend) and the backend's `uvicorn` command
  together for the app to work — see root `README.md`.

## Backend notes

- `src/backend/store.py` — the mock database: an in-memory `PartyStore`
  keyed by id, with methods for the queue transitions, code/phone lookup,
  and the derived fields (queue position, wait estimate, stats). Swap for a
  SQLAlchemy-backed store later; routes only depend on this class's public
  methods, not its internals.
- `src/backend/schemas.py` — pydantic request/response models; validation
  (non-blank name/phone, `party_size >= 1`) lives here via `field_validator`.
- `src/backend/deps.py` — `get_store()` FastAPI dependency; tests override it
  with a fresh `PartyStore` per test (see `tests/conftest.py`) so state never
  leaks between tests.
- `src/backend/routes/` — one router per resource (`parties`, `stats`,
  `status`), thin wrappers that translate store exceptions
  (`PartyNotFoundError` → 404, `InvalidTransitionError` → 409) into HTTP
  responses.
- Endpoints match `../openapi.yaml` exactly — check both when changing the
  API shape.
