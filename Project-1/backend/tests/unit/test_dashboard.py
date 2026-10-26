import datetime as dt

from tests.conftest import make_module, make_session, make_track


def test_empty_state(client, today):  # AC4.6
    d = client.get("/api/dashboard").json()
    assert d["empty"] is True
    assert d["tracks"] == [] and d["recent_sessions"] == []
    assert d["streak"] == {"current_days": 0, "longest_days": 0}
    assert len(d["weekly_trend"]) == 8
    assert d["week"]["hours"] == 0 and d["week"]["goal_hours"] == 5


def test_week_hours_vs_goal(client, today):  # AC4.1 (today = Wed 21 Oct 2026)
    t = make_track(client)
    make_session(client, t["id"], date="2026-10-19", minutes=90)  # Mon - this week
    make_session(client, t["id"], date="2026-10-21", minutes=60)  # Wed - this week
    make_session(client, t["id"], date="2026-10-18", minutes=600)  # Sun - last week
    d = client.get("/api/dashboard").json()
    assert d["today"] == "2026-10-21" and d["week"]["start"] == "2026-10-19"
    assert d["week"]["hours"] == 2.5 and d["week"]["percent"] == 50


def test_week_start_sunday(client, today):  # AC5.1 + AC4.1
    t = make_track(client)
    make_session(client, t["id"], date="2026-10-18", minutes=60)  # Sunday
    client.put(
        "/api/settings",
        json={"weekly_goal_hours": 2, "timezone": "Asia/Kolkata", "week_start": "sunday"},
    )
    d = client.get("/api/dashboard").json()
    assert d["week"]["start"] == "2026-10-18" and d["week"]["percent"] == 50


def test_streaks(client, today):  # AC4.2
    t = make_track(client)
    for day in (10, 11, 12, 13, 20, 21):
        make_session(client, t["id"], date=dt.date(2026, 10, day))
    assert client.get("/api/dashboard").json()["streak"] == {"current_days": 2, "longest_days": 4}


def test_streak_across_new_year(client, today):  # AC4.2
    today.set(dt.date(2027, 1, 1))
    t = make_track(client)
    for d in (dt.date(2026, 12, 30), dt.date(2026, 12, 31), dt.date(2027, 1, 1)):
        make_session(client, t["id"], date=d)
    assert client.get("/api/dashboard").json()["streak"]["current_days"] == 3


def test_per_track_progress(client, today):  # AC4.3
    a = make_track(client, "A", target=10, color="#111111")
    b = make_track(client, "B", target=4)
    m1, _ = make_module(client, a["id"], "m1"), make_module(client, a["id"], "m2")
    client.patch(f"/api/modules/{m1['id']}", json={"status": "done"})
    make_session(client, a["id"], minutes=150)
    tracks = {t["name"]: t for t in client.get("/api/dashboard").json()["tracks"]}
    assert tracks["A"] == {
        "track_id": a["id"],
        "name": "A",
        "color": "#111111",
        "hours": 2.5,
        "target_hours": 10,
        "target_percent": 25,
        "module_count": 2,
        "completion_percent": 50,
    }
    assert tracks["B"]["hours"] == 0 and tracks["B"]["track_id"] == b["id"]


def test_trend_last_8_weeks(client, today):  # AC4.4
    t = make_track(client)
    make_session(client, t["id"], date="2026-10-20", minutes=60)
    make_session(client, t["id"], date="2026-09-01", minutes=120)  # 8th week back starts 31 Aug
    trend = client.get("/api/dashboard").json()["weekly_trend"]
    assert trend[0] == {"week_start": "2026-08-31", "hours": 2.0}
    assert trend[-1] == {"week_start": "2026-10-19", "hours": 1.0}
    assert [w["hours"] for w in trend[1:-1]] == [0] * 6


def test_recent_five_newest_first(client, today):  # AC4.5
    t = make_track(client)
    ids = [make_session(client, t["id"], date=dt.date(2026, 10, d))["id"] for d in range(1, 8)]
    recent = client.get("/api/dashboard").json()["recent_sessions"]
    assert [r["id"] for r in recent] == list(reversed(ids))[:5]


def test_settings_timezone_drives_today(client):
    client.put(
        "/api/settings",
        json={"weekly_goal_hours": 5, "timezone": "Pacific/Kiritimati", "week_start": "monday"},
    )
    d = client.get("/api/dashboard").json()
    assert d["timezone"] == "Pacific/Kiritimati"
