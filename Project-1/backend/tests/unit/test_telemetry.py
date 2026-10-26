"""Observability NFR: key journey emits traces + metrics + logs sharing a trace_id,
and no topics / notes / tokens leak into any signal."""

import json
import logging

from fastapi.testclient import TestClient

from learnloop.main import create_app
from learnloop.telemetry import JsonFormatter
from tests.conftest import make_config

SECRET_TOPIC = "TOPIC-should-not-leak-7731"
SECRET_NOTES = "NOTES-should-not-leak-9912"
TOKEN = "tok-should-not-leak-4410"


def test_key_journey_signals_and_no_pii(today):
    app = create_app(make_config(token=TOKEN), telemetry_mode="memory")
    captured: list[str] = []

    class Capture(logging.Handler):
        def emit(self, record):
            captured.append(JsonFormatter().format(record))

    lg = logging.getLogger("learnloop")
    h = Capture()
    lg.addHandler(h)
    try:
        with TestClient(app) as c:
            auth = {"Authorization": f"Bearer {TOKEN}"}
            t = c.post("/api/tracks", json={"name": "A", "target_hours": 5}, headers=auth).json()
            r = c.post(
                "/api/sessions",
                headers=auth,
                json={
                    "track_id": t["id"],
                    "date": "2026-10-20",
                    "minutes": 45,
                    "topic": SECRET_TOPIC,
                    "notes": SECRET_NOTES,
                },
            )
            assert r.status_code == 201
            assert c.get("/api/dashboard").status_code == 200
            tel = app.state.telemetry
            spans = tel.span_exporter.get_finished_spans()
            logs = tel.log_exporter.get_finished_logs()
            metrics = tel.metric_reader.get_metrics_data()
    finally:
        lg.removeHandler(h)

    # --- traces: server span for the POST exists, with DB child spans ---
    post_spans = [s for s in spans if s.name == "POST /api/sessions"]
    assert post_spans, [s.name for s in spans]
    trace_id = format(post_spans[0].context.trace_id, "032x")
    assert any(s.attributes.get("db.system") for s in spans)

    # --- logs: JSON lines with the same trace_id ---
    logged = [json.loads(line) for line in captured]
    session_log = next(entry for entry in logged if entry["message"] == "session logged")
    assert session_log["trace_id"] == trace_id
    access = [
        entry
        for entry in logged
        if entry["message"] == "request" and entry["http_route"] == "/api/sessions"
    ]
    assert access and access[0]["trace_id"] == trace_id and access[0]["http_status_code"] == 201
    assert any(r.log_record.body == "session logged" for r in logs)

    # --- metrics: request counter, latency histogram, business counter ---
    names = {
        m.name for rm in metrics.resource_metrics for sm in rm.scope_metrics for m in sm.metrics
    }
    assert {
        "learnloop_http_requests",
        "learnloop_http_request_duration",
        "learnloop_sessions_logged",
    } <= names

    # --- privacy: nothing secret in any signal ---
    blob = (
        json.dumps(
            [
                {
                    "name": s.name,
                    "attrs": dict(s.attributes or {}),
                    "events": [dict(e.attributes or {}) for e in s.events],
                }
                for s in spans
            ]
            + [
                str(r.log_record.body)
                + json.dumps(dict(r.log_record.attributes or {}), default=str)
                for r in logs
            ]
            + captured,
            default=str,
        )
        + metrics.to_json()
    )
    for secret in (SECRET_TOPIC, SECRET_NOTES, TOKEN):
        assert secret not in blob
