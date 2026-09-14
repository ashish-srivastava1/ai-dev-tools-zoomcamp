import pytest
from fastapi.testclient import TestClient

from backend.deps import get_store
from backend.main import app
from backend.store import PartyStore


@pytest.fixture
def store() -> PartyStore:
    """A fresh, empty in-memory store for each test."""
    return PartyStore()


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
