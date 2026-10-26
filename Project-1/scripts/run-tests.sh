#!/bin/sh
# Runs the whole test suite. Used inside the `test` image (docker-compose.test.yml)
# and by CI. Needs INTEGRATION_DATABASE_URL for the integration tests.
set -eu
cd "$(dirname "$0")/.."

echo "==> backend: lint"
(cd backend && uv run ruff check . && uv run ruff format --check .)

echo "==> backend: unit tests"
(cd backend && uv run pytest -q)

echo "==> backend: integration tests (PostgreSQL)"
if [ -z "${INTEGRATION_DATABASE_URL:-}" ]; then
  echo "INTEGRATION_DATABASE_URL is not set" >&2
  exit 1
fi
(cd backend && uv run pytest -q -m integration)

echo "==> frontend: lint + tests"
(cd frontend && npm run lint && npm test)

echo "==> all tests passed"
