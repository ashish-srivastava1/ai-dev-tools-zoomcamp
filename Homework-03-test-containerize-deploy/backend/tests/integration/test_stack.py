"""A. Stack & infrastructure — the parts unit tests can't reach: the image
actually builds and boots, Postgres gates the app, and API writes really land
in Postgres (not a SQLite fallback)."""

import uuid

import pytest

from _stack import compose, psql

pytestmark = pytest.mark.integration


def test_health_endpoint_ok(api):
    response = api.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_db_service_is_healthy(stack):
    # The app only reached a serving state (the `stack` fixture waited on
    # /health) because Postgres passed its healthcheck first — depends_on:
    # service_healthy. Confirm the db container is reporting healthy.
    result = compose("ps", "db", "--format", "json", capture_output=True, text=True)
    assert '"Health":"healthy"' in result.stdout.replace(" ", "")


def test_api_writes_reach_postgres(api):
    # Prove the app is backed by Postgres: a party created over HTTP must be
    # visible when we query the Postgres container directly.
    token = uuid.uuid4().hex[:8]
    phone = f"555-{token}"
    created = api.post(
        "/api/parties",
        json={"name": f"PG-{token}", "party_size": 3, "phone_number": phone, "notes": ""},
    )
    assert created.status_code == 201, created.text

    count = psql(f"select count(*) from parties where phone_number = '{phone}'")
    assert count == "1"
