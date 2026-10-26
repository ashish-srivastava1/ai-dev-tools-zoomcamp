# On-call responder (on-call agent)

A small FastAPI service that **wakes up when Grafana fires an alert**. It gathers evidence,
then hands the incident to a headless coding agent that reproduces the bug with a failing
test, fixes it, and runs the tests. It's adapted from the HW4 incident responder, with
LearnLoop-specific queries, dedupe, resolve handling and git/PR automation.

```
Grafana alert (5xx ratio / p95 on the key journey)
   │  webhook POST http://host.docker.internal:8001/alerts
   ▼
responder.py ── dedupe / busy-guard ── telemetry_sources.py (Prometheus, Loki, Tempo)
   │                                        │ evidence -> ops/incidents/<id>/
   ▼                                        ▼
agent_runner.py ── claude -p "<prompt>" --permission-mode acceptEdits   (or AGENT_CMD / stub)
   │  reads AGENTS.md + ops/runbook.md → failing test → fix → uv run pytest
   │  (ONCALL_GIT=1) → branch fix/oncall-<id> → push → gh issue + PR "Closes #n"
   ▼
ops/incidents/<id>/incident.md  (report; marked resolved when Grafana sends "resolved")
```

## Run it (on the host, next to `docker compose up`)

```bash
cd Project-1/ops/oncall
uv sync
uv run uvicorn responder:app --host 0.0.0.0 --port 8001
curl http://localhost:8001/healthz
```

It has to run on the host, not in a container, because the coding agent edits the repository
and uses your `claude` / `git` / `gh` logins. Grafana (in compose) reaches it at
`http://host.docker.internal:8001/alerts`.

## Configuration

| Env var | Default | Meaning |
|---|---|---|
| `REPO_DIR` | `Project-1/` (two levels up) | Working directory for the agent |
| `INCIDENTS_DIR` | `$REPO_DIR/ops/incidents` | Where evidence and reports go |
| `PROM_URL` / `LOKI_URL` / `TEMPO_URL` | `http://localhost:9090` / `:3100` / `:3200` | Telemetry backends (ports published by compose) |
| `AGENT_CMD` | – | Explicit agent command; the prompt goes on stdin (e.g. `claude -p --permission-mode acceptEdits`) |
| `CLAUDE_PERMISSION_MODE` | `acceptEdits` | Used when `claude` is found on PATH |
| `AGENT_TIMEOUT` | `1200` | Seconds before the agent is stopped |
| `ONCALL_GIT` | `0` | `1` = the agent branches, commits, pushes and opens an issue + PR with `gh` |
| `DEDUPE_MINUTES` | `15` | Repeat notifications of the same alert within this window don't start a new agent |
| `ONCALL_LOKI_QUERY` | `{service_name="learnloop"} \| severity_text=~"(?i)error\|critical\|fatal"` | Error-log query |

With no `AGENT_CMD` and no `claude` on PATH, a **stub** answers instead, so the pipeline still
works end to end and simply escalates to a human.

## Behaviour

- **Firing alert:** creates `ops/incidents/<UTC-timestamp>-<alertname>/` containing
  `alert.json`, `metric.json`, `logs.json`, `traces.json`, `prompt.txt`,
  `agent-response.txt` and `incident.md`.
- **Repeat notification (same alertname + fingerprint):** counted as `repeats` on the open
  incident; no second agent is started.
- **Another real alert while an agent is running:** recorded as `skipped_agent_busy`. Two
  agents never edit the code at the same time.
- **Resolved notification:** the incident becomes `resolved` and `resolved.json` is written.
- **Test alerts** (label `test=true`, alertname `TestAlert`, or Grafana's "Test notification"):
  no evidence is gathered; the agent acknowledges and takes no action.
- `GET /incidents` and `GET /incidents/{id}` show live status.

Annotations it relies on, all optional: `summary`, `description`, `endpoint`, `window`,
`dashboard_url`, `runbook_url`. Labels: `alertname`, `service`, `severity`.

## Send a test alert

```bash
curl -s -X POST http://localhost:8001/alerts -H 'Content-Type: application/json' -d '{
  "status": "firing",
  "alerts": [{"status": "firing", "fingerprint": "manual-1",
    "labels": {"alertname": "LearnLoop key journey 5xx", "service": "learnloop", "severity": "critical"},
    "annotations": {"summary": "Users get errors on the dashboard", "endpoint": "GET /api/dashboard",
                    "window": "last 5m", "runbook_url": "ops/runbook.md"}}]}'
curl -s http://localhost:8001/incidents
```

On Windows PowerShell, use `Invoke-RestMethod -Method Post -ContentType 'application/json' -Body '<same json>' http://localhost:8001/alerts`.

## End-to-end demo

The full script is in [`../runbook.md`](../runbook.md#demo-alert--on-call-agent--fix). In short:
inject the bug, rebuild the app, generate traffic, the alert fires, the agent fixes the bug,
rebuild the app, and the alert resolves.

## Tests

```bash
uv run pytest -q     # parsing, dedupe, resolve, busy guard, prompt building, stub agent
```
