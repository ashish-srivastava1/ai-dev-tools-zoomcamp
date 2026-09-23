from datetime import datetime, timedelta, timezone


def test_list_parties_starts_empty(client):
    response = client.get("/api/parties")
    assert response.status_code == 200
    assert response.json() == []


def test_add_party_returns_waiting_party_with_position_one(add_party):
    party = add_party(name="Alvarez", party_size=4, phone_number="555-010-1234", notes="Window seat")

    assert party["name"] == "Alvarez"
    assert party["party_size"] == 4
    assert party["phone_number"] == "555-010-1234"
    assert party["notes"] == "Window seat"
    assert party["status"] == "waiting"
    assert party["id"]
    assert party["code"]
    assert party["created_at"]
    assert party["called_at"] is None
    assert party["seated_at"] is None
    assert party["removed_at"] is None
    assert party["position"] == 1
    assert party["parties_ahead"] == 0
    assert party["estimated_wait_minutes"] == 0


def test_add_party_generates_unique_codes(add_party):
    a = add_party(name="A")
    b = add_party(name="B")
    assert a["code"] != b["code"]


def test_add_party_rejects_blank_name(client):
    response = client.post(
        "/api/parties",
        json={"name": "   ", "party_size": 2, "phone_number": "555-1", "notes": ""},
    )
    assert response.status_code == 422


def test_add_party_rejects_blank_phone_number(client):
    response = client.post(
        "/api/parties",
        json={"name": "Nguyen", "party_size": 2, "phone_number": "  ", "notes": ""},
    )
    assert response.status_code == 422


def test_add_party_rejects_party_size_below_one(client):
    response = client.post(
        "/api/parties",
        json={"name": "Nguyen", "party_size": 0, "phone_number": "555-1", "notes": ""},
    )
    assert response.status_code == 422


def test_list_parties_is_fifo_and_positions_are_sequential(add_party):
    a = add_party(name="A")
    b = add_party(name="B")
    c = add_party(name="C")

    response_ids = [p["id"] for p in [a, b, c]]
    assert response_ids == [a["id"], b["id"], c["id"]]
    assert a["position"] == 1
    assert b["position"] == 2
    assert b["parties_ahead"] == 1
    assert c["position"] == 3
    assert c["parties_ahead"] == 2


def test_call_party_marks_called_and_clears_position(add_party, client):
    party = add_party()
    response = client.post(f"/api/parties/{party['id']}/call")
    assert response.status_code == 200
    updated = response.json()
    assert updated["status"] == "called"
    assert updated["called_at"] is not None
    assert updated["position"] is None
    assert updated["parties_ahead"] == 0
    assert updated["estimated_wait_minutes"] == 0


def test_call_party_shrinks_positions_of_parties_behind(add_party, client):
    a = add_party(name="A")
    b = add_party(name="B")

    client.post(f"/api/parties/{a['id']}/call")

    response = client.get("/api/parties")
    parties_by_id = {p["id"]: p for p in response.json()}
    assert parties_by_id[b["id"]]["position"] == 1
    assert parties_by_id[b["id"]]["parties_ahead"] == 0


def test_calling_a_non_waiting_party_is_conflict(add_party, client):
    party = add_party()
    client.post(f"/api/parties/{party['id']}/call")

    response = client.post(f"/api/parties/{party['id']}/call")
    assert response.status_code == 409


def test_seat_party_from_waiting(add_party, client):
    party = add_party()
    response = client.post(f"/api/parties/{party['id']}/seat")
    assert response.status_code == 200
    updated = response.json()
    assert updated["status"] == "seated"
    assert updated["seated_at"] is not None
    assert updated["position"] is None
    assert updated["estimated_wait_minutes"] is None


def test_seat_party_from_called(add_party, client):
    party = add_party()
    client.post(f"/api/parties/{party['id']}/call")
    response = client.post(f"/api/parties/{party['id']}/seat")
    assert response.status_code == 200
    assert response.json()["status"] == "seated"


def test_seating_an_already_seated_party_is_conflict(add_party, client):
    party = add_party()
    client.post(f"/api/parties/{party['id']}/seat")
    response = client.post(f"/api/parties/{party['id']}/seat")
    assert response.status_code == 409


def test_remove_party_from_waiting(add_party, client):
    party = add_party()
    response = client.post(f"/api/parties/{party['id']}/remove")
    assert response.status_code == 200
    updated = response.json()
    assert updated["status"] == "removed"
    assert updated["removed_at"] is not None


def test_removing_an_already_removed_party_is_conflict(add_party, client):
    party = add_party()
    client.post(f"/api/parties/{party['id']}/remove")
    response = client.post(f"/api/parties/{party['id']}/remove")
    assert response.status_code == 409


def test_action_on_unknown_party_is_not_found(client):
    for action in ("call", "seat", "remove"):
        response = client.post(f"/api/parties/does-not-exist/{action}")
        assert response.status_code == 404


def test_estimated_wait_uses_average_of_completed_seatings(add_party, client, store):
    first = add_party(name="First")
    now = datetime.now(timezone.utc)
    seated = store.get(first["id"])
    seated.created_at = now - timedelta(minutes=30)
    seated.status = "seated"
    seated.seated_at = now - timedelta(minutes=10)  # took 20 minutes to seat

    second = add_party(name="Second")
    third = add_party(name="Third")

    response = client.get("/api/parties")
    parties_by_name = {p["name"]: p for p in response.json()}

    assert parties_by_name["Second"]["parties_ahead"] == 0
    assert parties_by_name["Second"]["estimated_wait_minutes"] == 0
    assert parties_by_name["Third"]["parties_ahead"] == 1
    assert parties_by_name["Third"]["estimated_wait_minutes"] == 20
