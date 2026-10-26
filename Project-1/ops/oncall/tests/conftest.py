import pytest
from fastapi.testclient import TestClient

import agent_runner
import responder
import telemetry_sources


def firing(alertname="LearnLoop key journey 5xx", fingerprint="fp1", status="firing", **ann):
    return {
        "receiver": "oncall-agent",
        "status": status,
        "alerts": [{
            "status": status,
            "labels": {"alertname": alertname, "service": "learnloop", "severity": "critical"},
            "annotations": {"summary": "Users are getting errors", "endpoint": "GET /api/dashboard",
                            "window": "last 5m", "description": "5xx ratio above 5%",
                            "dashboard_url": "http://localhost:3001/d/learnloop",
                            "runbook_url": "ops/runbook.md", **ann},
            "startsAt": "2026-10-26T10:00:00Z",
            "fingerprint": fingerprint,
        }],
    }


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setattr(responder, "INCIDENTS_DIR", tmp_path / "incidents")
    monkeypatch.setattr(responder, "REPO_DIR", tmp_path)
    monkeypatch.setattr(responder, "_dispatch", lambda target, *args: target(*args))
    calls = {"agent": [], "gather": 0}

    def fake_gather():
        calls["gather"] += 1
        return {"metric": {"error_5xx_by_route_5m": [{"labels": {"http_route": "/api/dashboard"},
                                                      "value": "12"}]},
                "logs": {"lines": ['{"level":"error","message":"unhandled error"}']},
                "traces": {"matches": [{"trace_id": "abc"}]}}

    def fake_agent(prompt, incident, workdir, timeout=None):
        calls["agent"].append({"prompt": prompt, "incident": incident, "workdir": workdir})
        return "Investigated.\nFixed: guarded completion_percent against zero modules."

    monkeypatch.setattr(telemetry_sources, "gather_all", fake_gather)
    monkeypatch.setattr(agent_runner, "run_agent", fake_agent)
    monkeypatch.setattr(agent_runner, "agent_mode", lambda: "fake")
    monkeypatch.delenv("ONCALL_GIT", raising=False)
    responder.reset_state()
    yield calls, tmp_path / "incidents"
    responder.reset_state()


@pytest.fixture
def client(env):
    return TestClient(responder.app)
