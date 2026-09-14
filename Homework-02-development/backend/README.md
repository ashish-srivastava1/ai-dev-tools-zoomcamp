# backend

FastAPI backend for TableTurn. See the repo root [README](../README.md) and
[AGENTS.md](../AGENTS.md) for how this fits together, and
[`../openapi.yaml`](../openapi.yaml) for the API contract.

```
uv run uvicorn backend.main:app --reload --port 8000
uv run pytest
```

Data is currently an in-memory mock (`src/backend/store.py`) — swapped for
SQLite via SQLAlchemy later in the homework.
