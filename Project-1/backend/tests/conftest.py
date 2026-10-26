import datetime as dt
import os

os.environ.setdefault("TELEMETRY_EXPORTER", "none")

import pytest
from fastapi.testclient import TestClient

from learnloop import logic
from learnloop.config import Config
from learnloop.main import create_app
from learnloop.routes import sessions as sessions_route


def make_config(url: str = "sqlite://", token: str | None = None) -> Config:
    return Config(
        database_url=url, write_token=token, app_env="test", static_dir=None, version="test"
    )


@pytest.fixture
def client():
    app = create_app(make_config(), telemetry_mode="none")
    with TestClient(app) as c:
        yield c


@pytest.fixture
def secured_client():
    app = create_app(make_config(token="s3cret"), telemetry_mode="none")
    with TestClient(app) as c:
        yield c


@pytest.fixture
def today(monkeypatch):
    """Freeze 'today' (in the user's timezone) to a known date."""
    fixed = {"value": dt.date(2026, 10, 21)}  # a Wednesday

    def fake_today(tz_name, now=None):
        return fixed["value"]

    monkeypatch.setattr(logic, "today_in", fake_today)
    monkeypatch.setattr(sessions_route, "today_in", fake_today)

    class Setter:
        def set(self, d: dt.date):
            fixed["value"] = d

        @property
        def value(self):
            return fixed["value"]

    return Setter()


def make_track(c, name="AI Dev Tools", target=20, **extra):
    r = c.post("/api/tracks", json={"name": name, "target_hours": target, **extra})
    assert r.status_code == 201, r.text
    return r.json()


def make_module(c, track_id, title="Module 1", **extra):
    r = c.post(f"/api/tracks/{track_id}/modules", json={"title": title, **extra})
    assert r.status_code == 201, r.text
    return r.json()


def make_session(c, track_id, date="2026-10-20", minutes=60, topic="Docker", **extra):
    r = c.post(
        "/api/sessions",
        json={"track_id": track_id, "date": str(date), "minutes": minutes, "topic": topic, **extra},
    )
    assert r.status_code == 201, r.text
    return r.json()
