from tests.conftest import make_track


def test_default_settings(client):  # AC5.1
    assert client.get("/api/settings").json() == {
        "weekly_goal_hours": 5,
        "timezone": "Asia/Kolkata",
        "week_start": "monday",
    }


def test_update_settings(client):  # AC5.1
    body = {"weekly_goal_hours": 8, "timezone": "Europe/London", "week_start": "sunday"}
    assert client.put("/api/settings", json=body).json() == body
    assert client.get("/api/settings").json() == body
    assert client.get("/api/dashboard").json()["week"]["goal_hours"] == 8


def test_invalid_settings(client):
    for bad in (
        {"weekly_goal_hours": 0},
        {"timezone": "Mars/Base"},
        {"week_start": "friday"},
        {"weekly_goal_hours": 200},
    ):
        body = {"weekly_goal_hours": 5, "timezone": "Asia/Kolkata", "week_start": "monday", **bad}
        assert client.put("/api/settings", json=body).status_code == 422, bad


def test_writes_open_without_token(client):
    make_track(client)


def test_write_token_required_when_configured(secured_client):  # NFR security
    c = secured_client
    body = {"name": "A", "target_hours": 1}
    assert c.post("/api/tracks", json=body).status_code == 401
    assert (
        c.post("/api/tracks", json=body, headers={"Authorization": "Bearer wrong"}).status_code
        == 401
    )
    ok = c.post("/api/tracks", json=body, headers={"Authorization": "Bearer s3cret"})
    assert ok.status_code == 201
    # reads stay open
    assert c.get("/api/tracks").status_code == 200
    assert c.get("/api/dashboard").status_code == 200
    for method, url in (
        ("patch", f"/api/tracks/{ok.json()['id']}"),
        ("put", "/api/settings"),
        ("delete", "/api/sessions/1"),
        ("delete", "/api/modules/1"),
    ):
        assert (
            getattr(c, method)(url, json={}).status_code == 401
            if method != "delete"
            else getattr(c, method)(url).status_code == 401
        )


def test_validation_errors_use_detail_shape(client):
    r = client.post("/api/tracks", json={"name": "", "target_hours": 1})
    assert r.status_code == 422 and isinstance(r.json()["detail"], list)
