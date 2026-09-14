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

## Deploying (free): Render + Turso

Render's free web service has no persistent disk, so the SQLite file
would be wiped on every restart. [Turso](https://turso.tech) is a
SQLite-compatible database (libSQL) with a real free-forever tier, so it's
the fix — a ~3-line config change, not a rewrite.

**1. Create a Turso database** (you'll need your own free Turso account —
install their CLI and follow https://docs.turso.tech/quickstart):

```
turso db create tableturn
turso db show tableturn --url          # → TURSO_DATABASE_URL, looks like libsql://tableturn-<you>.turso.io
turso db tokens create tableturn       # → TURSO_AUTH_TOKEN
```

**2. Create a Render web service** (you'll need your own free Render
account, no card required — https://render.com):

- New → Web Service → connect this GitHub repo
- **Root Directory:** `Homework-02-development/backend`
- **Build Command:** `pip install uv && uv sync --extra turso`
- **Start Command:** `uv run uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- **Environment variables:** add `TURSO_DATABASE_URL` and `TURSO_AUTH_TOKEN`
  from step 1 — paste them directly into Render's dashboard, not anywhere
  they'd end up committed to git.
- **Health check path:** `/health`

Once deployed, Render gives you a URL like
`https://tableturn-backend.onrender.com` — set that as `VITE_API_BASE_URL`
for the frontend (see `frontend/.env.example`), and once the frontend has
its own deployed URL, tighten `main.py`'s CORS `allow_origins` from `*` to
that origin.

The `turso` extra (`sqlalchemy-libsql`) is only needed for this — it's not
in the default dependency set, and it has no Windows wheel (Linux/macOS
only), so local dev on Windows is unaffected either way.
