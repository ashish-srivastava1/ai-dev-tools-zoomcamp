# Homework 4 - DevOps and Observability for AI-Built Apps

My answers and how to reproduce them. All work is in this repository.

## Answers

| Q | Question | Answer |
|---|----------|--------|
| 1 | What does the health check return? | **`{"status":"ok"}`** |
| 2 | HTTP status the metric records for `standard-1001` | **200** |
| 3 | HTTP status the metric shows for `standard-1002` | **404** |
| 4 | Alert state after the 404 lookup (no 5xx) | **Normal** |
| 5 | What did the agent respond? (last line) | see below |
| 6 | What was the problem? | **The express delivery date calculation tried to use a day that does not exist in that month.** |

### Q5 - agent response (last line)

The responder launched the coding assistant in headless mode and it replied
(last line):

> No action required: this was a test notification with no incident to fix.

Full response: `incident-response/incidents/20261003T094311Z-ResponderTest/agent-response.txt`.

## What was built

- **Q2** - `app/telemetry.py`: OpenTelemetry metrics, logs and traces for order
  lookups. The `http_server_requests` counter carries `http_route`,
  `http_method` and `http_status_code`. Console export by default
  (`TELEMETRY_EXPORTER=console`), switchable to OTLP.
- **Q3** - `observability/` + `compose.yaml`: OpenTelemetry Collector fans
  metrics to Prometheus, logs to Loki and traces to Tempo. Grafana is
  provisioned with the three datasources and the "Order Tracker - Requests &
  Errors" dashboard.
- **Q4** - `observability/grafana/provisioning/alerting/alert-rules.yaml`: a 5xx
  alert that uses `or vector(0)` + `noDataState: OK`, so quiet periods read as
  Normal instead of No Data. Annotations carry the endpoint, window and
  dashboard link.
- **Q5** - `incident-response/`: a service receiving Grafana webhooks at
  `POST /alerts` (:8001). It records the alert, gathers metric/logs/traces and
  launches a coding assistant in headless mode (pluggable: `AGENT_CMD`, then
  `claude` on PATH, then a stub).
- **Q6** - `contactpoints.yaml` + `policies.yaml` wire the alert to the
  responder. The fix for the express 500 is in `app/main.py`
  (`timedelta(days=2)` instead of `replace(day=day + 2)`). See the recorded
  incident under `incident-response/incidents/`.

## Reproduce

```bash
# 1. Start the stack
docker compose up --build -d --wait

# 2. Lookups
curl http://localhost:8000/healthz                      # {"status":"ok"}
curl -i http://localhost:8000/api/orders/standard-1001  # 200
curl -i http://localhost:8000/api/orders/standard-1002  # 404
curl -i http://localhost:8000/api/orders/express-1002   # 200 after the fix

# 3. Grafana (admin/admin). Published on 3001 to avoid a local clash on 3000.
#    http://localhost:3001  -> dashboard + alert

# 4. Responder (host)
cd incident-response && uv run uvicorn responder:app --host 0.0.0.0 --port 8001

# 5. Q5 test alert
curl -X POST http://localhost:8001/alerts \
  -H 'Content-Type: application/json' \
  -d '{"alerts":[{"status":"firing","labels":{"alertname":"ResponderTest","test":"true"},"annotations":{"summary":"Test notification; no incident to fix"}}]}'
curl http://localhost:8001/incidents
```

## Evidence

Screenshots in `docs/evidence/`: Q3 dashboard (metrics + logs), Q4 alert Normal,
Q6 alert Firing. Recorded incident with telemetry context and resolution in
`incident-response/incidents/`.

## Note on the coding assistant

The responder launches the assistant in headless mode behind a pluggable
interface. In this submission the stub backend was used (it escalates), and the
Q6 fix was applied by hand following the responder's escalation. Setting
`AGENT_CMD="claude -p --permission-mode acceptEdits"` (with an authenticated
`claude` CLI) makes the responder apply such fixes automatically.
