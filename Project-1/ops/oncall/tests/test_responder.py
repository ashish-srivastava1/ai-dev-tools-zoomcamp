import json

import responder
from tests.conftest import firing


def test_healthz(client):
    body = client.get("/healthz").json()
    assert body["status"] == "ok" and body["git_enabled"] is False


def test_firing_alert_runs_agent_and_writes_evidence(client, env):
    calls, incidents = env
    r = client.post("/alerts", json=firing()).json()
    [res] = r["results"]
    assert res["status"] == "accepted"
    inc_dir = incidents / res["incident"]
    for name in ("alert.json", "metric.json", "logs.json", "traces.json", "prompt.txt",
                 "agent-response.txt", "incident.md"):
        assert (inc_dir / name).exists(), name
    assert len(calls["agent"]) == 1 and calls["gather"] == 1
    assert "unhandled error" in (inc_dir / "prompt.txt").read_text()
    report = (inc_dir / "incident.md").read_text()
    assert "Fixed: guarded completion_percent" in report
    detail = client.get(f"/incidents/{res['incident']}").json()
    assert detail["status"] == "agent_done"
    assert not responder._agent_busy.is_set()


def test_repeat_notifications_are_deduped(client, env):
    calls, _ = env
    first = client.post("/alerts", json=firing()).json()["results"][0]["incident"]
    dup = client.post("/alerts", json=firing()).json()["results"][0]
    assert dup == {"status": "duplicate", "incident": first}
    assert len(calls["agent"]) == 1
    assert client.get(f"/incidents/{first}").json()["repeats"] == 1


def test_different_alert_is_not_deduped(client, env):
    calls, _ = env
    client.post("/alerts", json=firing())
    client.post("/alerts", json=firing(alertname="LearnLoop key journey latency",
                                       fingerprint="fp2"))
    assert len(calls["agent"]) == 2


def test_resolved_marks_incident_resolved(client, env):
    _, incidents = env
    inc_id = client.post("/alerts", json=firing()).json()["results"][0]["incident"]
    r = client.post("/alerts", json=firing(status="resolved")).json()["results"][0]
    assert r == {"status": "resolved", "incident": inc_id}
    assert client.get(f"/incidents/{inc_id}").json()["status"] == "resolved"
    assert (incidents / inc_id / "resolved.json").exists()
    assert "Resolved:** 20" in (incidents / inc_id / "incident.md").read_text()
    # after resolve, a new firing opens a new incident (no dedupe)
    again = client.post("/alerts", json=firing()).json()["results"][0]
    assert again["status"] == "accepted" and again["incident"] != inc_id


def test_resolved_without_incident_is_recorded(client):
    r = client.post("/alerts", json=firing(status="resolved")).json()["results"][0]
    assert r["status"] == "resolved_unknown"


def test_busy_guard_skips_concurrent_real_alerts(client, env, monkeypatch):
    calls, _ = env
    monkeypatch.setattr(responder, "_dispatch", lambda target, *args: None)  # agent "still running"
    first = client.post("/alerts", json=firing()).json()["results"][0]
    assert first["status"] == "accepted" and responder._agent_busy.is_set()
    other = client.post("/alerts", json=firing(alertname="Other", fingerprint="z")).json()
    assert other["results"][0]["status"] == "skipped_agent_busy"


def test_test_alert_skips_evidence_and_busy_guard(client, env):
    calls, _ = env
    responder._agent_busy.set()
    r = client.post("/alerts", json=firing(alertname="TestAlert")).json()["results"][0]
    assert r["status"] == "accepted"
    assert calls["gather"] == 0 and len(calls["agent"]) == 1


def test_git_flag_reaches_prompt(client, env, monkeypatch):
    calls, _ = env
    monkeypatch.setenv("ONCALL_GIT", "1")
    client.post("/alerts", json=firing())
    assert "gh issue create" in calls["agent"][0]["prompt"]


def test_last_webhook_saved_and_empty_payload_ignored(client, env):
    _, incidents = env
    assert client.post("/alerts", json={"alerts": []}).json()["status"] == "ignored"
    assert json.loads((incidents / "last-webhook.json").read_text()) == {"alerts": []}


def test_agent_runner_stub(monkeypatch):
    import importlib

    import agent_runner

    importlib.reload(agent_runner)  # undo fixture patches if any
    monkeypatch.delenv("AGENT_CMD", raising=False)
    monkeypatch.setattr(agent_runner.shutil, "which", lambda _: None)
    out = agent_runner.run_agent("p", {"is_test": True, "alertname": "TestAlert"}, ".")
    assert out.splitlines()[-1].startswith("No action required")
    assert agent_runner.agent_mode().startswith("stub")
    monkeypatch.setenv("AGENT_CMD", "cat")
    assert agent_runner.run_agent("hello prompt", {}, ".") == "hello prompt"
