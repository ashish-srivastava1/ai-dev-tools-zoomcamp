"""D/E. A thin end-to-end smoke layer over real HTTP + Postgres. The business
logic is already covered exhaustively by the unit suite; here we just confirm
the main flows and the error contract hold against the deployed stack.

Assertions target each test's own party (unique data) rather than global
counts, since the session shares one Postgres."""

import pytest

pytestmark = pytest.mark.integration


def test_party_lifecycle_add_call_seat(api, add_party):
    party = add_party()
    pid = party["id"]
    assert party["status"] == "waiting"

    called = api.post(f"/api/parties/{pid}/call")
    assert called.status_code == 200
    assert called.json()["status"] == "called"
    assert called.json()["called_at"] is not None

    seated = api.post(f"/api/parties/{pid}/seat")
    assert seated.status_code == 200
    assert seated.json()["status"] == "seated"
    assert seated.json()["seated_at"] is not None


def test_public_status_lookup_by_code_and_phone(api, add_party):
    party = add_party()

    by_code = api.get("/api/status", params={"code": party["code"]})
    assert by_code.status_code == 200
    assert by_code.json()["id"] == party["id"]

    by_phone = api.get("/api/status", params={"phone_number": party["phone_number"]})
    assert by_phone.status_code == 200
    assert by_phone.json()["id"] == party["id"]


def test_validation_transition_and_notfound_errors(api, add_party):
    # 422 — invalid body.
    bad = api.post(
        "/api/parties",
        json={"name": "   ", "party_size": 0, "phone_number": "", "notes": ""},
    )
    assert bad.status_code == 422

    # 409 — invalid transition (calling an already-called party).
    party = add_party()
    api.post(f"/api/parties/{party['id']}/call")
    conflict = api.post(f"/api/parties/{party['id']}/call")
    assert conflict.status_code == 409

    # 404 — unknown lookup code.
    missing = api.get("/api/status", params={"code": "ZZZZ"})
    assert missing.status_code == 404


def test_stats_waiting_count_increments(api, add_party):
    before = api.get("/api/stats")
    assert before.status_code == 200
    baseline = before.json()["waiting_count"]

    add_party()

    after = api.get("/api/stats").json()
    assert after["waiting_count"] == baseline + 1
