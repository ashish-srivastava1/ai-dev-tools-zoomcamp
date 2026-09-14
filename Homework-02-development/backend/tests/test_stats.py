from datetime import datetime, timedelta, timezone


def test_stats_start_at_zero_with_no_average(client):
    response = client.get("/api/stats")
    assert response.status_code == 200
    assert response.json() == {
        "waiting_count": 0,
        "called_count": 0,
        "avg_wait_today_minutes": None,
    }


def test_stats_counts_waiting_and_called(add_party, client):
    a = add_party(name="A")
    add_party(name="B")
    client.post(f"/api/parties/{a['id']}/call")

    response = client.get("/api/stats")
    body = response.json()
    assert body["waiting_count"] == 1
    assert body["called_count"] == 1


def test_stats_excludes_seated_and_removed_from_active_counts(add_party, client):
    a = add_party(name="A")
    b = add_party(name="B")
    client.post(f"/api/parties/{a['id']}/seat")
    client.post(f"/api/parties/{b['id']}/remove")

    response = client.get("/api/stats")
    body = response.json()
    assert body["waiting_count"] == 0
    assert body["called_count"] == 0


def test_avg_wait_today_reflects_seated_parties_today(add_party, client, store):
    party = add_party(name="A")
    now = datetime.now(timezone.utc)
    record = store.get(party["id"])
    record.created_at = now - timedelta(minutes=25)
    record.status = "seated"
    record.seated_at = now - timedelta(minutes=5)  # 20 minute wait

    response = client.get("/api/stats")
    assert response.json()["avg_wait_today_minutes"] == 20


def test_avg_wait_today_ignores_seatings_from_a_previous_day(add_party, client, store):
    party = add_party(name="A")
    now = datetime.now(timezone.utc)
    record = store.get(party["id"])
    record.created_at = now - timedelta(days=1, minutes=30)
    record.status = "seated"
    record.seated_at = now - timedelta(days=1, minutes=10)

    response = client.get("/api/stats")
    assert response.json()["avg_wait_today_minutes"] is None
