"""Incident responder.

Receives Grafana alert webhooks at ``POST /alerts`` (port 8001). For each
firing alert it:

1. Records the alert and gathers the context needed to understand the problem
   - recent logs (Loki), recent traces (Tempo) and the 5xx metric (Prometheus)
   - saving everything under ``incidents/<id>/``.
2. Launches a coding assistant in headless mode (see ``agent_runner``) to
   investigate and, for a real incident, fix the root cause in the repo.
3. Stores the assistant's answer so it can be read back.

The webhook returns immediately (so Grafana does not time out); the agent runs
in a background thread. Poll ``GET /incidents/{id}`` for the result.
"""

import datetime as dt
import json
import os
import threading
import time
from pathlib import Path

import httpx
from fastapi import FastAPI, Request

import agent_runner

HERE = Path(__file__).resolve().parent
REPO_DIR = Path(os.getenv("REPO_DIR", HERE.parent))
INCIDENTS_DIR = Path(os.getenv("INCIDENTS_DIR", HERE / "incidents"))
INCIDENTS_DIR.mkdir(parents=True, exist_ok=True)

PROM_URL = os.getenv("PROM_URL", "http://localhost:9090")
LOKI_URL = os.getenv("LOKI_URL", "http://localhost:3100")
TEMPO_URL = os.getenv("TEMPO_URL", "http://localhost:3200")

app = FastAPI(title="Incident Responder")

# In-memory index of incidents handled this run.
_incidents: dict[str, dict] = {}

# Guard so a repeated/flapping alert does not launch several agents at once
# (they would edit the same files concurrently). A real incident is skipped
# while an agent is already running; test alerts always run.
_agent_busy = threading.Event()


def _now_id() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _gather_logs(endpoint: str) -> dict:
    """Recent app logs from Loki (last 30 minutes)."""
    end = time.time_ns()
    start = end - 30 * 60 * 1_000_000_000
    try:
        r = httpx.get(
            f"{LOKI_URL}/loki/api/v1/query_range",
            params={
                "query": '{service_name="order-tracker"}',
                "start": start,
                "end": end,
                "limit": 50,
                "direction": "backward",
            },
            timeout=10,
        )
        return r.json()
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}


def _gather_traces() -> dict:
    """Recent traces from Tempo."""
    try:
        r = httpx.get(f"{TEMPO_URL}/api/search", params={"limit": 20}, timeout=10)
        return r.json()
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}


def _gather_metric() -> dict:
    """Current 5xx count from Prometheus."""
    try:
        r = httpx.get(
            f"{PROM_URL}/api/v1/query",
            params={
                "query": 'sum by (http_route, http_status_code) '
                '(http_server_requests_total{http_status_code=~"5.."})'
            },
            timeout=10,
        )
        return r.json()
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}


def _build_prompt(incident: dict, context: dict) -> str:
    """Prompt handed to the headless coding assistant."""
    if incident.get("is_test"):
        return (
            "You are an on-call incident responder running in headless mode.\n"
            "You received a TEST alert from Grafana. There is no real incident "
            "and no code to change.\n"
            f"Alert: {json.dumps(incident.get('alert_labels', {}))}\n"
            f"Summary: {incident.get('summary')}\n\n"
            "Acknowledge the test, confirm the responder pipeline works, and "
            "take no action. End with a single clear last line stating no "
            "action was required."
        )
    return (
        "You are an on-call incident responder running in headless mode, with "
        f"access to the order-tracker repository at {REPO_DIR}.\n\n"
        "A Grafana alert just fired for 5xx errors.\n"
        f"- Affected endpoint: {incident.get('endpoint')}\n"
        f"- Time window: {incident.get('window')}\n"
        f"- Summary: {incident.get('summary')}\n"
        f"- Description: {incident.get('description')}\n\n"
        "Evidence gathered from telemetry:\n"
        f"METRIC (5xx counts):\n{json.dumps(context.get('metric', {}), indent=2)[:2000]}\n\n"
        f"LOGS (recent):\n{json.dumps(context.get('logs', {}), indent=2)[:3000]}\n\n"
        f"TRACES (recent):\n{json.dumps(context.get('traces', {}), indent=2)[:2000]}\n\n"
        "Investigate the root cause in the application code, fix it, and keep "
        "the change minimal and correct. Then summarise what was wrong and what "
        "you changed. End with a single clear last line stating the outcome."
    )


def _handle_incident(incident_id: str, incident: dict) -> None:
    """Background worker: gather context, run the agent, save results."""
    inc_dir = INCIDENTS_DIR / incident_id
    inc_dir.mkdir(parents=True, exist_ok=True)

    context = {}
    if not incident.get("is_test"):
        context = {
            "metric": _gather_metric(),
            "logs": _gather_logs(incident.get("endpoint", "")),
            "traces": _gather_traces(),
        }
        (inc_dir / "metric.json").write_text(json.dumps(context["metric"], indent=2))
        (inc_dir / "logs.json").write_text(json.dumps(context["logs"], indent=2))
        (inc_dir / "traces.json").write_text(json.dumps(context["traces"], indent=2))

    prompt = _build_prompt(incident, context)
    (inc_dir / "prompt.txt").write_text(prompt)

    _incidents[incident_id]["status"] = "agent_running"
    _incidents[incident_id]["agent_backend"] = agent_runner.agent_mode()
    print(f"[responder] incident {incident_id}: launching agent "
          f"({_incidents[incident_id]['agent_backend']})", flush=True)

    _agent_busy.set()
    try:
        answer = agent_runner.run_agent(prompt, incident, str(REPO_DIR))
    finally:
        _agent_busy.clear()

    (inc_dir / "agent-response.txt").write_text(answer)
    last_line = next(
        (ln.strip() for ln in reversed(answer.splitlines()) if ln.strip()), ""
    )
    _incidents[incident_id].update(
        status="done", agent_response=answer, agent_last_line=last_line
    )
    print(f"[responder] incident {incident_id} done. Last line: {last_line}", flush=True)


@app.get("/healthz")
def healthz():
    return {"status": "ok", "agent_backend": agent_runner.agent_mode()}


@app.post("/alerts")
async def alerts(request: Request):
    payload = await request.json()
    (INCIDENTS_DIR / "last-webhook.json").write_text(json.dumps(payload, indent=2))

    firing = [a for a in payload.get("alerts", []) if a.get("status") == "firing"]
    if not firing:
        return {"status": "ignored", "reason": "no firing alerts in payload"}

    handled = []
    for alert in firing:
        labels = alert.get("labels", {})
        annotations = alert.get("annotations", {})
        alertname = labels.get("alertname", "alert")
        is_test = labels.get("test") == "true" or "no incident" in (
            annotations.get("summary", "").lower()
        )

        incident_id = f"{_now_id()}-{alertname}"
        incident = {
            "id": incident_id,
            "alertname": alertname,
            "is_test": is_test,
            "endpoint": annotations.get("endpoint"),
            "window": annotations.get("window"),
            "summary": annotations.get("summary"),
            "description": annotations.get("description"),
            "dashboard_url": annotations.get("dashboard_url"),
            "alert_labels": labels,
            "received_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        }

        inc_dir = INCIDENTS_DIR / incident_id
        inc_dir.mkdir(parents=True, exist_ok=True)
        (inc_dir / "alert.json").write_text(json.dumps(alert, indent=2))

        # A real incident is skipped while an agent is already working, so a
        # flapping alert does not spawn concurrent agents editing the same code.
        if not is_test and _agent_busy.is_set():
            _incidents[incident_id] = {**incident, "status": "skipped_agent_busy"}
            handled.append(incident_id)
            print(f"[responder] skipped incident {incident_id}: agent busy", flush=True)
            continue

        _incidents[incident_id] = {**incident, "status": "accepted"}
        threading.Thread(
            target=_handle_incident, args=(incident_id, incident), daemon=True
        ).start()
        handled.append(incident_id)
        print(f"[responder] accepted incident {incident_id} (test={is_test})", flush=True)

    return {"status": "accepted", "incidents": handled}


@app.get("/incidents")
def list_incidents():
    return {
        "incidents": [
            {"id": i, "status": v.get("status"), "last_line": v.get("agent_last_line")}
            for i, v in _incidents.items()
        ]
    }


@app.get("/incidents/{incident_id}")
def get_incident(incident_id: str):
    return _incidents.get(incident_id, {"error": "unknown incident"})
