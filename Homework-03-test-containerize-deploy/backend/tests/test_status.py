def test_lookup_by_code(add_party, client):
    party = add_party(name="Alvarez")
    response = client.get("/api/status", params={"code": party["code"]})
    assert response.status_code == 200
    assert response.json()["id"] == party["id"]


def test_lookup_by_code_is_case_insensitive(add_party, client):
    party = add_party(name="Alvarez")
    response = client.get("/api/status", params={"code": party["code"].lower()})
    assert response.status_code == 200
    assert response.json()["id"] == party["id"]


def test_lookup_by_phone_number(add_party, client):
    party = add_party(name="Alvarez", phone_number="555-010-9999")
    response = client.get("/api/status", params={"phone_number": "555-010-9999"})
    assert response.status_code == 200
    assert response.json()["id"] == party["id"]


def test_lookup_by_phone_number_returns_most_recent_match(add_party, client):
    add_party(name="Older", phone_number="555-010-9999")
    newer = add_party(name="Newer", phone_number="555-010-9999")

    response = client.get("/api/status", params={"phone_number": "555-010-9999"})
    assert response.json()["id"] == newer["id"]


def test_lookup_unknown_code_is_not_found(client):
    response = client.get("/api/status", params={"code": "ZZZZ"})
    assert response.status_code == 404


def test_lookup_unknown_phone_is_not_found(client):
    response = client.get("/api/status", params={"phone_number": "000-000-0000"})
    assert response.status_code == 404


def test_lookup_without_code_or_phone_is_invalid(client):
    response = client.get("/api/status")
    assert response.status_code == 422


def test_lookup_reflects_current_status(add_party, client):
    party = add_party(name="Alvarez")
    client.post(f"/api/parties/{party['id']}/call")

    response = client.get("/api/status", params={"code": party["code"]})
    assert response.json()["status"] == "called"
