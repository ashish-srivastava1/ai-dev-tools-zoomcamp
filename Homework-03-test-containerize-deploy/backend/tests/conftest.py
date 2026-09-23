import os

# Must be set before `backend.db` is first imported (below, transitively via
# `backend.deps`) — it reads DATABASE_URL at import time to build the app's
# module-level engine. Without this, every test run's `TestClient(app)`
# lifespan would create/touch the real tableturn.db file on disk (harmless,
# since tests never route data through it, but pointless).
os.environ.setdefault("DATABASE_URL", "sqlite://")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.deps import get_store
from backend.main import app
from backend.models import Base
from backend.store import PartyStore


@pytest.fixture
def store() -> PartyStore:
    """A fresh, empty database (in-memory SQLite) for each test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # one shared connection, so the in-memory DB survives across the test
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield PartyStore(session)
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def client(store: PartyStore) -> TestClient:
    app.dependency_overrides[get_store] = lambda: store
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def add_party(client: TestClient):
    """Helper to add a party via the API and return the parsed response body."""

    def _add(name="Alvarez", party_size=4, phone_number="555-010-1234", notes=""):
        response = client.post(
            "/api/parties",
            json={
                "name": name,
                "party_size": party_size,
                "phone_number": phone_number,
                "notes": notes,
            },
        )
        assert response.status_code == 201, response.text
        return response.json()

    return _add
