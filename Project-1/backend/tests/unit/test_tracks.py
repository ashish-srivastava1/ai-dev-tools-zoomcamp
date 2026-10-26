from tests.conftest import make_session, make_track


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_create_and_list_track(client):  # AC1.1
    t = make_track(client, "AI Dev Tools", 20, description="Zoomcamp", color="#ff0000")
    assert t["name"] == "AI Dev Tools" and t["archived"] is False and t["color"] == "#ff0000"
    assert [x["id"] for x in client.get("/api/tracks").json()] == [t["id"]]


def test_default_color(client):
    assert make_track(client)["color"] == "#4f46e5"


def test_duplicate_name_case_insensitive_rejected(client):  # AC1.2
    make_track(client, "LLM Agents")
    r = client.post("/api/tracks", json={"name": "  llm agents ", "target_hours": 5})
    assert r.status_code == 422
    assert "already exists" in r.json()["detail"]


def test_invalid_target_rejected(client):  # AC1.2
    for bad in (0, -1):
        r = client.post("/api/tracks", json={"name": "X", "target_hours": bad})
        assert r.status_code == 422


def test_invalid_color_and_blank_name_rejected(client):
    assert (
        client.post(
            "/api/tracks", json={"name": "X", "target_hours": 1, "color": "red"}
        ).status_code
        == 422
    )
    assert client.post("/api/tracks", json={"name": "   ", "target_hours": 1}).status_code == 422


def test_edit_track(client):  # AC1.3
    t = make_track(client)
    r = client.patch(
        f"/api/tracks/{t['id']}",
        json={"name": "Renamed", "target_hours": 30, "description": "d", "color": "#00ff00"},
    )
    assert r.status_code == 200
    body = r.json()
    assert (body["name"], body["target_hours"], body["description"], body["color"]) == (
        "Renamed",
        30,
        "d",
        "#00ff00",
    )


def test_rename_to_existing_name_rejected(client):
    make_track(client, "A")
    b = make_track(client, "B")
    assert client.patch(f"/api/tracks/{b['id']}", json={"name": "a"}).status_code == 422
    # renaming to itself with different case is fine
    assert client.patch(f"/api/tracks/{b['id']}", json={"name": "b"}).status_code == 200


def test_empty_or_null_patch_rejected(client):
    t = make_track(client)
    assert client.patch(f"/api/tracks/{t['id']}", json={}).status_code == 422
    assert client.patch(f"/api/tracks/{t['id']}", json={"name": None}).status_code == 422


def test_archive_hides_track_but_keeps_sessions(client, today):  # AC1.4
    t = make_track(client)
    make_session(client, t["id"])
    assert client.patch(f"/api/tracks/{t['id']}", json={"archived": True}).status_code == 200
    assert client.get("/api/tracks").json() == []
    assert len(client.get("/api/tracks?include_archived=true").json()) == 1
    assert client.get("/api/sessions").json()["total"] == 1
    dash = client.get("/api/dashboard").json()
    assert dash["tracks"] == [] and dash["empty"] is True


def test_unknown_track_404(client):
    assert client.get("/api/tracks/999").status_code == 404
    assert client.patch("/api/tracks/999", json={"name": "x"}).status_code == 404
