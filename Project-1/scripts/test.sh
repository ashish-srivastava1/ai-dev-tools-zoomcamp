#!/bin/sh
# Single command for the whole test suite (backend lint + unit, integration on
# Postgres, frontend lint + tests) - all inside Docker.
set -u
cd "$(dirname "$0")/.."
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from tests
status=$?
docker compose -f docker-compose.test.yml down -v >/dev/null 2>&1
exit $status
