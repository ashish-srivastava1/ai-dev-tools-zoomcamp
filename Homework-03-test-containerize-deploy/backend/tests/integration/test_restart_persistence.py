"""C. Persistence — the point of moving to Postgres + a volume. Data written
through the API must survive the app process restarting (server-side state
lives in Postgres, not in the app container)."""

import pytest

from _stack import BASE_URL, compose, wait_for_health

pytestmark = pytest.mark.integration


def test_data_survives_app_restart(api, add_party):
    party = add_party(name="Persist Me")
    phone = party["phone_number"]

    # Restart just the app container; Postgres (and its volume) stay up.
    compose("restart", "app")
    wait_for_health(f"{BASE_URL}/health")

    # The party is still retrievable after the app came back — it was never
    # held in the app's memory.
    lookup = api.get("/api/status", params={"phone_number": phone})
    assert lookup.status_code == 200, lookup.text
    assert lookup.json()["id"] == party["id"]
    assert lookup.json()["name"] == "Persist Me"
