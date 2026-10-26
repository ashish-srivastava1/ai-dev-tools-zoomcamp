# LearnLoop backend

FastAPI + SQLAlchemy 2. Managed with `uv`.

```bash
uv run uvicorn learnloop.main:app --reload --port 8000   # http://localhost:8000/docs
uv run pytest                                           # unit tests (SQLite)
INTEGRATION_DATABASE_URL=postgresql+psycopg://learnloop:learnloop@localhost:5432/learnloop \
  uv run pytest -m integration                          # integration tests (Postgres)
uv run ruff check .
```

Configuration (env vars): `DATABASE_URL`, `WRITE_TOKEN`, `APP_ENV`, `STATIC_DIR`,
`TELEMETRY_EXPORTER` (`none`/`console`/`otlp`), `OTEL_EXPORTER_OTLP_ENDPOINT`,
`OTEL_SERVICE_NAME`.
