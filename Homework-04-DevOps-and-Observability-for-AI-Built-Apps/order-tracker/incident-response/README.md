# Incident Responder

A small service that receives Grafana alert webhooks and launches a coding
assistant in headless mode to investigate (and, for a real incident, fix) the
problem.

## Run

The responder runs on the host (not in Compose) so the coding assistant can
reach the repository and its own credentials. It talks to the telemetry stack
over the published localhost ports.

```bash
cd incident-response
uv run uvicorn responder:app --host 0.0.0.0 --port 8001
```

Health check:

```bash
curl http://localhost:8001/healthz
```

## What it does on `POST /alerts`

1. Parses the Grafana webhook and records the alert under `incidents/<id>/`.
2. For a real (non-test) alert, gathers context and saves it next to the alert:
   - `metric.json`  - 5xx counts from Prometheus
   - `logs.json`    - recent app logs from Loki
   - `traces.json`  - recent traces from Tempo
3. Builds a prompt (`prompt.txt`) and launches the coding assistant in a
   background thread. The answer is saved to `agent-response.txt`.
4. Returns `{"status": "accepted", "incidents": [...]}` immediately so Grafana's
   webhook does not time out.

Read a result:

```bash
curl http://localhost:8001/incidents            # list
curl http://localhost:8001/incidents/<id>       # one incident + agent answer
```

## Choosing the coding assistant

The assistant is pluggable (see `agent_runner.py`), resolved in this order:

1. `AGENT_CMD` env var - an explicit command, prompt passed on stdin, e.g.
   `AGENT_CMD="claude -p --permission-mode acceptEdits"`.
2. `claude` on PATH - invoked as `claude -p <prompt> --permission-mode acceptEdits`.
3. A built-in stub - used when no assistant is installed yet, so the service is
   testable. Wiring the real agent later is a one-line env change.

## Configuration (env vars)

| Var | Default | Purpose |
|-----|---------|---------|
| `REPO_DIR` | parent of this dir | Repo the agent works in |
| `INCIDENTS_DIR` | `./incidents` | Where incidents are saved |
| `PROM_URL` | `http://localhost:9090` | Prometheus |
| `LOKI_URL` | `http://localhost:3100` | Loki |
| `TEMPO_URL` | `http://localhost:3200` | Tempo |
| `AGENT_CMD` | (unset) | Explicit agent command |
