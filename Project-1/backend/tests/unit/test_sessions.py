import datetime as dt

from tests.conftest import make_module, make_session, make_track


def test_log_session(client, today):  # AC3.1
    t = make_track(client)
    m = make_module(client, t["id"])
    s = make_session(client, t["id"], module_id=m["id"], notes="compose healthchecks")
    assert s["module_id"] == m["id"] and s["minutes"] == 60 and s["notes"] == "compose healthchecks"
    dash = client.get("/api/dashboard").json()
    assert dash["week"]["hours"] == 1.0
    assert dash["recent_sessions"][0]["id"] == s["id"]


def test_minutes_limits(client, today):  # AC3.2
    t = make_track(client)
    base = {"track_id": t["id"], "date": "2026-10-20", "topic": "x"}
    for bad in (0, 601, -5):
        assert client.post("/api/sessions", json={**base, "minutes": bad}).status_code == 422
    for ok in (1, 600):
        assert client.post("/api/sessions", json={**base, "minutes": ok}).status_code == 201


def test_future_date_rejected_using_user_timezone(client, today):  # AC3.2
    t = make_track(client)
    tomorrow = today.value + dt.timedelta(days=1)
    r = client.post(
        "/api/sessions",
        json={"track_id": t["id"], "date": str(tomorrow), "minutes": 30, "topic": "x"},
    )
    assert r.status_code == 422 and "future" in r.json()["detail"]
    assert make_session(client, t["id"], date=today.value)["date"] == str(today.value)


def test_unknown_or_archived_track_rejected(client, today):  # AC3.2
    r = client.post(
        "/api/sessions", json={"track_id": 99, "date": "2026-10-20", "minutes": 5, "topic": "x"}
    )
    assert r.status_code == 422
    t = make_track(client)
    client.patch(f"/api/tracks/{t['id']}", json={"archived": True})
    r = client.post(
        "/api/sessions",
        json={"track_id": t["id"], "date": "2026-10-20", "minutes": 5, "topic": "x"},
    )
    assert r.status_code == 422 and "archived" in r.json()["detail"]


def test_module_must_belong_to_track(client, today):  # AC3.2
    a, b = make_track(client, "A"), make_track(client, "B")
    mb = make_module(client, b["id"])
    r = client.post(
        "/api/sessions",
        json={
            "track_id": a["id"],
            "module_id": mb["id"],
            "date": "2026-10-20",
            "minutes": 5,
            "topic": "x",
        },
    )
    assert r.status_code == 422


def test_topic_and_notes_limits(client, today):
    t = make_track(client)
    base = {"track_id": t["id"], "date": "2026-10-20", "minutes": 5}
    assert client.post("/api/sessions", json={**base, "topic": ""}).status_code == 422
    assert client.post("/api/sessions", json={**base, "topic": "x" * 121}).status_code == 422
    assert (
        client.post("/api/sessions", json={**base, "topic": "x", "notes": "n" * 2001}).status_code
        == 422
    )


def test_edit_and_delete_update_totals(client, today):  # AC3.3
    t = make_track(client)
    s = make_session(client, t["id"], minutes=60)
    r = client.patch(f"/api/sessions/{s['id']}", json={"minutes": 120, "topic": "K8s"})
    assert r.status_code == 200 and r.json()["topic"] == "K8s"
    assert client.get("/api/dashboard").json()["week"]["hours"] == 2.0
    assert client.delete(f"/api/sessions/{s['id']}").status_code == 204
    assert client.get("/api/dashboard").json()["week"]["hours"] == 0
    assert client.get(f"/api/sessions/{s['id']}").status_code == 404


def test_edit_validates_too(client, today):  # AC3.3 uses AC3.2 rules
    t = make_track(client)
    s = make_session(client, t["id"])
    assert client.patch(f"/api/sessions/{s['id']}", json={"minutes": 0}).status_code == 422
    assert client.patch(f"/api/sessions/{s['id']}", json={"date": "2030-01-01"}).status_code == 422
    assert client.patch(f"/api/sessions/{s['id']}", json={}).status_code == 422


def test_moving_session_to_other_track_drops_module(client, today):
    a, b = make_track(client, "A"), make_track(client, "B")
    m = make_module(client, a["id"])
    s = make_session(client, a["id"], module_id=m["id"])
    r = client.patch(f"/api/sessions/{s['id']}", json={"track_id": b["id"]})
    assert r.status_code == 200 and r.json()["module_id"] is None


def test_list_filters_order_and_pagination(client, today):  # AC3.4
    a, b = make_track(client, "A"), make_track(client, "B")
    for day in range(1, 23):
        make_session(client, a["id"], date=dt.date(2026, 10, min(day, 21)), topic=f"t{day}")
    make_session(client, b["id"], date="2026-10-05")

    page1 = client.get("/api/sessions").json()
    assert page1["total"] == 23 and len(page1["items"]) == 20 and page1["page_size"] == 20
    dates = [i["date"] for i in page1["items"]]
    assert dates == sorted(dates, reverse=True)
    page2 = client.get("/api/sessions?page=2").json()
    assert len(page2["items"]) == 3

    only_b = client.get(f"/api/sessions?track_id={b['id']}").json()
    assert only_b["total"] == 1
    ranged = client.get("/api/sessions?from=2026-10-04&to=2026-10-06").json()
    assert {i["date"] for i in ranged["items"]} == {"2026-10-04", "2026-10-05", "2026-10-06"}
    assert client.get("/api/sessions?page_size=101").status_code == 422
