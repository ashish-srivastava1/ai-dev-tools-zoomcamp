# Observability: LearnLoop

`docker compose up --build` (from `Project-1/`) starts the app together with:

| Component | Role | URL |
|---|---|---|
| OpenTelemetry Collector | Receives OTLP gRPC (`:4317`) from the app and fans signals out | internal |
| Prometheus | Metrics (scrapes the collector's `:8889`) | http://localhost:9090 |
| Tempo | Traces | http://localhost:3200 |
| Loki | Logs (OTLP ingest) | http://localhost:3100 |
| Grafana | UI: dashboard, Explore, alerting | http://localhost:3001 (admin/admin) |

## What is instrumented
The key user journey is **log a session (`POST /api/sessions`) → dashboard reloads (`GET /api/dashboard`)**.

- **Traces:** FastAPI server spans plus SQLAlchemy child spans for each query, all under `service.name=learnloop`.
- **Metrics:** the collector re-exposes the app's custom metrics to Prometheus:
  - `learnloop_http_requests_total{http_route, http_method, http_status_code}`: a counter
  - `learnloop_http_request_duration_seconds_bucket|_sum|_count{...}`: a latency histogram
  - `learnloop_sessions_logged_total`: a business counter

  Resource labels are added as well: `service_name`, `deployment_environment` and `service_version`.
- **Logs:** structured JSON on stdout, plus OTLP to Loki. Every request log and every "session logged" event carries the `trace_id` and `span_id` of the request, so one request can be followed across all three signals.

## Following one request across all signals
1. Open the **LearnLoop › LearnLoop - Key journey** dashboard (`/d/learnloop`).
2. In **Recent traces**, click a trace. Tempo shows the server span and its DB spans.
3. Click **Logs for this span**. Grafana runs `{service_name="learnloop"} | trace_id="<id>"` in Loki.
4. You can also go the other way. In **Application logs**, expand a line and click the `TraceID` link to open the trace.

## Privacy (spec section 6)
- Only ids, counts, durations, routes and status codes are recorded.
- The app never logs a session's `topic` or `notes`, the write token, or the DB URL. Request bodies and headers are not captured.
- A unit test checks this: `backend/tests/unit/test_telemetry.py` posts a session with marker values and asserts they appear in no span, log or metric.
- The collector also deletes `authorization`, query and DB-parameter attributes as a second line of defence (`attributes/scrub`).

## Alerts on user impact
The rules are provisioned in `grafana/provisioning/alerting/alert-rules.yaml`, in the *LearnLoop* folder. Neither is based on CPU or memory.

| Alert | Fires when | Severity |
|---|---|---|
| **LearnLoop key journey 5xx** | More than 5 % of key-journey requests return 5xx over 5 min, with at least 1 failure | critical, `for: 0s` |
| **LearnLoop key journey latency** | Key-journey p95 latency is above 1 s over 5 min | warning, `for: 1m` |

Quiet periods evaluate to **Normal**, not No Data, because of `or vector(0)` and `noDataState: OK`.

Both alerts go to the contact point `learnloop-oncall-agent`, a webhook at `http://host.docker.internal:8001/alerts`, which is the on-call responder in `../oncall/`.

**Label and annotation contract:**
- Labels: `alertname`, `service=learnloop`, `severity`, `journey=log-session`
- Annotations: `summary`, `description`, `endpoint`, `window`, `dashboard_url`, `runbook_url`

### Triggering an alert by hand
To check the pipeline without a real failure, open Grafana → *Alerting → Contact points → learnloop-oncall-agent → Test*. This sends a test notification.

For a real failure, use the chaos script in `../chaos/`, which injects a bug that makes the key journey return 500s. Then generate some traffic:

```powershell
# PowerShell
1..30 | % { try { Invoke-WebRequest http://localhost:8000/api/dashboard -UseBasicParsing | Out-Null } catch {} ; Start-Sleep -Milliseconds 300 }
```
```bash
# bash
for i in $(seq 30); do curl -s -o /dev/null -w "%{http_code}\n" localhost:8000/api/dashboard; sleep 0.3; done
```

Watch *Alerting → Alert rules*. The rule turns Pending, then Firing within about 20 s.

**Note:** `increase()` needs two samples of a series. The very first 5xx creates the series, so keep the traffic going for 15–20 s rather than sending a single request.
