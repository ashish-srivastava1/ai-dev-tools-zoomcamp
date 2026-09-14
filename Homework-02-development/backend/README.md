# backend

FastAPI backend for TableTurn. See the repo root [README](../README.md) and
[AGENTS.md](../AGENTS.md) for how this fits together, and
[`../openapi.yaml`](../openapi.yaml) for the API contract.

```
uv run uvicorn backend.main:app --reload --port 8000
uv run pytest
```

Data is persisted via SQLAlchemy (`src/backend/store.py`, `models.py`,
`db.py`) to a SQLite file at `tableturn.db`, created automatically on
first run. Delete it to reset all data. `DATABASE_URL` (env var) overrides
the default if you want to point at a different database — the store
doesn't rely on any SQLite-specific behavior.
