"""LearnLoop on-call responder.

Grafana posts alert notifications to ``POST /alerts`` (port 8001). For each FIRING alert:

1. dedupe - the same alert (alertname + fingerprint) only opens one incident per
   ``DEDUPE_MINUTES`` window; Grafana's repeat notifications are recorded, not re-run;
2. record the alert and gather evidence - 5xx/latency metrics (Prometheus), error logs
   (Loki) and error traces (Tempo) - into ``ops/incidents/<id>/``;
3. wake a headless coding agent (see ``agent_runner``) with a prompt that tells it to
   reproduce with a failing test, fix the root cause, run the tests and (if ONCALL_GIT=1)
   open an issue + PR;
4. save the answer and an ``incident.md`` report.

RESOLVED notifications mark the matching incident resolved. Only one agent runs at a time
(busy guard); real alerts arriving while it is busy are recorded as ``skipped_agent_busy``.
The webhook returns immediately; the agent runs in a background thread.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import threading
from pathlib import Path

from fastapi import FastAPI, Request

import agent_runner
import incident as inc
import telemetry_sources

HERE = Path(__file__).resolve().parent
REPO_DIR = Path(os.getenv("REPO_DIR", HERE.parent.parent))  # Project-1/
INCIDENTS_DIR = Path(os.getenv("INCIDENTS_DIR", REPO_DIR / "ops" / "incidents"))
DEDUPE_MINUTES = float(os.getenv("DEDUPE_MINUTES", "15"))


def git_enabled() -> bool:
    return os.getenv("ONCALL_GIT", "0") == "1"


app = FastAPI(title="LearnLoop on-call responder")

_lock = threading.Lock()
_incidents: dict[str, dict] = {}
_last_seen: dict[str, dt.datetime] = {}  # alert key -> when it last opened an incident
_open_by_key: dict[str, str] = {}  # alert key -> incident id (for resolve)
_agent_busy = threading.Event()


def reset_state() -> None:
    """Used by tests."""
    with _lock:
        _incidents.clear()
        _last_seen.clear()
        _open_by_key.clear()
    _agent_busy.clear()


def _now() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


def _write(inc_dir: Path, name: str, data) -> None:
    inc_dir.mkdir(parents=True, exist_ok=True)
    text = data if isinstance(data, str) else json.dumps(data, indent=2, default=str)
    (inc_dir / name).write_text(text, encoding="utf-8")


def _dispatch(target, *args) -> None:
    """Run work in the background (tests monkeypatch this to run inline)."""
    threading.Thread(target=target, args=args, daemon=True).start()


def _handle(incident_id: str, alert: inc.Alert) -> None:
    inc_dir = INCIDENTS_DIR / incident_id
    record = _incidents[incident_id]
    context: dict = {}
    try:
        if not alert.is_test:
            record["status"] = "gathering_evidence"
            context = telemetry_sources.gather_all()
            _write(inc_dir, "metric.json", context.get("metric", {}))
            _write(inc_dir, "logs.json", context.get("logs", {}))
            _write(inc_dir, "traces.json", context.get("traces", {}))

        prompt = inc.build_prompt(alert, context, str(REPO_DIR), incident_id, git_enabled())
        _write(inc_dir, "prompt.txt", prompt)
        _write(inc_dir, "incident.md", inc.render_report(record, context))

        record["status"] = "agent_running"
        record["agent_backend"] = agent_runner.agent_mode()
        print(f"[oncall] {incident_id}: launching agent ({record['agent_backend']})", flush=True)
        answer = agent_runner.run_agent(prompt, record, str(REPO_DIR))
        _write(inc_dir, "agent-response.txt", answer)
        last = next((ln.strip() for ln in reversed(answer.splitlines()) if ln.strip()), "")
        record.update(agent_last_line=last)
        if record.get("status") != "resolved":
            record["status"] = "agent_done"
        _append_report(inc_dir, record, context)
        print(f"[oncall] {incident_id}: done - {last}", flush=True)
    finally:
        if not alert.is_test:
            _agent_busy.clear()


def _append_report(inc_dir: Path, record: dict, context: dict) -> None:
    """Re-render the header but keep anything the agent wrote under 'Agent findings'."""
    path = inc_dir / "incident.md"
    findings = ""
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        marker = "## Agent findings"
        if marker in existing:
            findings = existing.split(marker, 1)[1]
    report = inc.render_report(record, context)
    if findings.strip() and "_The agent appends its findings here._" not in findings:
        report = report.split("## Agent findings", 1)[0] + "## Agent findings" + findings
    path.write_text(report, encoding="utf-8")


@app.get("/healthz")
def healthz():
    return {"status": "ok", "agent_backend": agent_runner.agent_mode(),
            "git_enabled": git_enabled(), "incidents_dir": str(INCIDENTS_DIR)}


@app.post("/alerts")
async def alerts(request: Request):
    payload = await request.json()
    INCIDENTS_DIR.mkdir(parents=True, exist_ok=True)
    _write(INCIDENTS_DIR, "last-webhook.json", payload)

    results = []
    now = _now()
    for alert in inc.parse_alerts(payload):
        if alert.status == "resolved":
            results.append(_resolve(alert, now))
            continue

        with _lock:
            if not alert.is_test and inc.is_duplicate(_last_seen, alert, now, DEDUPE_MINUTES):
                open_id = _open_by_key.get(alert.key)
                if open_id in _incidents:
                    _incidents[open_id]["repeats"] = _incidents[open_id].get("repeats", 0) + 1
                results.append({"status": "duplicate", "incident": open_id})
                continue

            incident_id = inc.incident_id(alert, now)
            while incident_id in _incidents:
                incident_id += "-x"
            record = {
                "id": incident_id,
                "alertname": alert.alertname,
                "key": alert.key,
                "is_test": alert.is_test,
                "labels": alert.labels,
                "annotations": alert.annotations,
                "received_at": now.isoformat(),
                "resolved_at": None,
                "repeats": 0,
            }
            if not alert.is_test and _agent_busy.is_set():
                record["status"] = "skipped_agent_busy"
                _incidents[incident_id] = record
                _write(INCIDENTS_DIR / incident_id, "alert.json", alert.to_dict())
                results.append({"status": "skipped_agent_busy", "incident": incident_id})
                continue

            record["status"] = "accepted"
            _incidents[incident_id] = record
            if not alert.is_test:
                _agent_busy.set()
                _last_seen[alert.key] = now
                _open_by_key[alert.key] = incident_id

        _write(INCIDENTS_DIR / incident_id, "alert.json", alert.to_dict())
        print(f"[oncall] accepted {incident_id} (test={alert.is_test})", flush=True)
        _dispatch(_handle, incident_id, alert)
        results.append({"status": "accepted", "incident": incident_id})

    if not results:
        return {"status": "ignored", "reason": "no alerts in payload"}
    return {"status": "ok", "results": results}


def _resolve(alert: inc.Alert, now: dt.datetime) -> dict:
    with _lock:
        incident_id = _open_by_key.pop(alert.key, None)
        _last_seen.pop(alert.key, None)
        if not incident_id or incident_id not in _incidents:
            return {"status": "resolved_unknown", "alert": alert.alertname}
        record = _incidents[incident_id]
        record["status"] = "resolved"
        record["resolved_at"] = now.isoformat()
    inc_dir = INCIDENTS_DIR / incident_id
    _write(inc_dir, "resolved.json", alert.to_dict())
    _append_report(inc_dir, record, {})
    print(f"[oncall] {incident_id} resolved", flush=True)
    return {"status": "resolved", "incident": incident_id}


@app.get("/incidents")
def list_incidents():
    return {"incidents": [
        {"id": i, "status": r.get("status"), "alert": r.get("alertname"),
         "repeats": r.get("repeats", 0), "last_line": r.get("agent_last_line")}
        for i, r in _incidents.items()
    ]}


@app.get("/incidents/{incident_id}")
def get_incident(incident_id: str):
    return _incidents.get(incident_id, {"error": "unknown incident"})
