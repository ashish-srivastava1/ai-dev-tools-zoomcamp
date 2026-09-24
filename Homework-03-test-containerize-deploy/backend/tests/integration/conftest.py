"""Integration-test harness: brings the real docker-compose stack up once for
the session, then tears it down.

Unlike the unit suite (in-process app + in-memory SQLite, see
`../conftest.py`), these tests are pure black-box: they only speak HTTP to the
running container and, where they need to prove persistence, shell into the
Postgres container. Nothing here imports the backend package.

Requires Docker with the Compose plugin on PATH. Run with:

    uv run --project backend pytest -m integration
"""

from __future__ import annotations

import uuid

import httpx
import pytest

from _stack import BASE_URL, compose, wait_for_health


@pytest.fixture(scope="session")
def stack() -> str:
    """Build and start the compose stack for the whole test session.

    Yields the app's base URL. Tears the stack down (and wipes the DB volume)
    afterwards so a run never leaks state into the next one.
    """
    compose("up", "-d", "--build")
    try:
        wait_for_health(f"{BASE_URL}/health")
        yield BASE_URL
    finally:
        compose("down", "-v")


@pytest.fixture
def api(stack: str):
    """An HTTP client pointed at the running stack."""
    with httpx.Client(base_url=stack, timeout=15.0) as client:
        yield client


@pytest.fixture
def add_party(api: httpx.Client):
    """Add a party via the API with unique data (the stack's Postgres is shared
    across the session, so tests must not collide) and return the response body.
    """

    def _add(**overrides) -> dict:
        token = uuid.uuid4().hex[:8]
        body = {
            "name": f"IT-{token}",
            "party_size": 2,
            "phone_number": f"555-{token}",
            "notes": "",
        }
        body.update(overrides)
        response = api.post("/api/parties", json=body)
        assert response.status_code == 201, response.text
        return response.json()

    return _add
