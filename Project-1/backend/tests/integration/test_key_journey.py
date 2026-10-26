"""End-to-end API workflows against a real PostgreSQL (run with `pytest -m integration`)."""

import datetime as dt

import pytest
from fastapi.testclient import TestClient

from learnloop import logic
from learnloop.main import create_app
from tests.conftest import make_config
from tests.integration.conftest import URL

pytestmark = pytest.mark.integration


def test_key_journey_log_session_updates_dashboard(pg_client):
    c = pg_client
    today = logic.today_in("Asia/Kolkata")

    assert c.get("/health").json() == {"status": "ok"}
    assert c.get("/api/dashboard").json()["empty"] is True

    track = c.post("/api/tracks", json={"name": "AI Dev Tools Zoomcamp", "target_hours": 40})
    assert track.status_code == 201
    tid = track.json()["id"]
    mods = [
        c.post(f"/api/tracks/{tid}/modules", json={"title": t}).json()
        for t in ("Workflow", "Development", "Deployment", "DevOps")
    ]
    c.patch(f"/api/modules/{mods[0]['id']}", json={"status": "done"})

    s1 = c.post(
        "/api/sessions",
        json={
            "track_id": tid,
            "module_id": mods[1]["id"],
            "date": str(today),
            "minutes": 90,
            "topic": "FastAPI",
        },
    )
    assert s1.status_code == 201
    s2 = c.post(
        "/api/sessions",
        json={
            "track_id": tid,
            "date": str(today - dt.timedelta(days=1)),
            "minutes": 30,
            "topic": "Docker",
        },
    )
    assert s2.status_code == 201

    d = c.get("/api/dashboard").json()
    assert d["empty"] is False
    assert d["streak"] == {"current_days": 2, "longest_days": 2}
    assert d["tracks"][0]["hours"] == 2.0
    assert d["tracks"][0]["target_percent"] == 5
    assert d["tracks"][0]["completion_percent"] == 25
    assert d["recent_sessions"][0]["id"] == s1.json()["id"]
    assert len(d["weekly_trend"]) == 8


def test_case_insensitive_unique_name_enforced_by_postgres(pg_client):
    c = pg_client
    assert c.post("/api/tracks", json={"name": "Agents", "target_hours": 1}).status_code == 201
    assert c.post("/api/tracks", json={"name": "AGENTS", "target_hours": 1}).status_code == 422


def test_delete_module_keeps_session_on_postgres(pg_client):
    c = pg_client
    tid = c.post("/api/tracks", json={"name": "T", "target_hours": 1}).json()["id"]
    mid = c.post(f"/api/tracks/{tid}/modules", json={"title": "M"}).json()["id"]
    sid = c.post(
        "/api/sessions",
        json={"track_id": tid, "module_id": mid, "date": "2026-01-05", "minutes": 10, "topic": "x"},
    ).json()["id"]
    assert c.delete(f"/api/modules/{mid}").status_code == 204
    assert c.get(f"/api/sessions/{sid}").json()["module_id"] is None


def test_data_persists_across_app_restarts(pg_client):
    c = pg_client
    c.post("/api/tracks", json={"name": "Persistent", "target_hours": 3})
    c.put(
        "/api/settings",
        json={"weekly_goal_hours": 7, "timezone": "Europe/Berlin", "week_start": "sunday"},
    )
    # A brand-new app instance (as after a redeploy) sees the same data.
    with TestClient(create_app(make_config(URL), telemetry_mode="none")) as fresh:
        assert [t["name"] for t in fresh.get("/api/tracks").json()] == ["Persistent"]
        assert fresh.get("/api/settings").json()["weekly_goal_hours"] == 7


def test_pagination_and_filters_on_postgres(pg_client):
    c = pg_client
    tid = c.post("/api/tracks", json={"name": "P", "target_hours": 10}).json()["id"]
    for i in range(25):
        c.post(
            "/api/sessions",
            json={
                "track_id": tid,
                "date": f"2026-02-{(i % 28) + 1:02d}",
                "minutes": 5,
                "topic": f"t{i}",
            },
        )
    page = c.get("/api/sessions?page=2&page_size=20").json()
    assert page["total"] == 25 and len(page["items"]) == 5
    feb = c.get("/api/sessions?from=2026-02-01&to=2026-02-03").json()
    assert feb["total"] == 3
