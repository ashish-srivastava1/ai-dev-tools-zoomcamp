from tests.conftest import make_module, make_session, make_track


def test_modules_listed_in_position_order(client):  # AC2.1
    t = make_track(client)
    a = make_module(client, t["id"], "Intro")
    b = make_module(client, t["id"], "Docker")
    mods = client.get(f"/api/tracks/{t['id']}/modules").json()
    assert [m["id"] for m in mods] == [a["id"], b["id"]]
    assert [m["position"] for m in mods] == [0, 1]
    assert mods[0]["status"] == "not_started"


def test_status_change_and_completion(client, today):  # AC2.2
    t = make_track(client)
    mods = [make_module(client, t["id"], f"M{i}") for i in range(3)]
    r = client.patch(f"/api/modules/{mods[0]['id']}", json={"status": "done"})
    assert r.status_code == 200 and r.json()["status"] == "done"
    track = client.get("/api/dashboard").json()["tracks"][0]
    assert track["module_count"] == 3 and track["completion_percent"] == 33


def test_invalid_status_rejected(client):
    t = make_track(client)
    m = make_module(client, t["id"])
    assert client.patch(f"/api/modules/{m['id']}", json={"status": "finished"}).status_code == 422


def test_completion_zero_when_no_modules(client, today):  # AC2.2
    make_track(client)
    assert client.get("/api/dashboard").json()["tracks"][0]["completion_percent"] == 0


def test_reorder(client):  # AC2.3
    t = make_track(client)
    a, b, c = (make_module(client, t["id"], n) for n in "abc")
    r = client.put(
        f"/api/tracks/{t['id']}/modules/order", json={"module_ids": [c["id"], a["id"], b["id"]]}
    )
    assert r.status_code == 200
    assert [m["title"] for m in r.json()] == ["c", "a", "b"]


def test_reorder_must_include_all_modules(client):
    t = make_track(client)
    a, b = make_module(client, t["id"], "a"), make_module(client, t["id"], "b")
    url = f"/api/tracks/{t['id']}/modules/order"
    assert client.put(url, json={"module_ids": [a["id"]]}).status_code == 422
    assert client.put(url, json={"module_ids": [a["id"], a["id"]]}).status_code == 422
    assert client.put(url, json={"module_ids": [a["id"], b["id"], 999]}).status_code == 422


def test_delete_module_keeps_sessions(client, today):  # AC2.3
    t = make_track(client)
    m = make_module(client, t["id"])
    s = make_session(client, t["id"], module_id=m["id"])
    assert client.delete(f"/api/modules/{m['id']}").status_code == 204
    assert client.get(f"/api/tracks/{t['id']}/modules").json() == []
    assert client.get(f"/api/sessions/{s['id']}").json()["module_id"] is None


def test_new_module_appended_after_reorder(client):
    t = make_track(client)
    make_module(client, t["id"], "a")
    assert make_module(client, t["id"], "b")["position"] == 1


def test_module_404s(client):
    assert client.get("/api/tracks/42/modules").status_code == 404
    assert client.patch("/api/modules/42", json={"title": "x"}).status_code == 404
    assert client.delete("/api/modules/42").status_code == 404
