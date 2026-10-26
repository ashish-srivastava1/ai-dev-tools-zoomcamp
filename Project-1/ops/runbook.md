# LearnLoop on-call runbook

LearnLoop pages on **user impact** for the key journey (spec section 7):
**log a session (`POST /api/sessions`) → load the dashboard (`GET /api/dashboard`)**.
CPU and memory are never paged on.

| Alert | Condition (5 min window) | What users see |
|---|---|---|
| **5xx on key journey** | 5xx ratio on `POST /api/sessions` or `GET /api/dashboard` > 5 % | "Could not load dashboard" / "Session not saved" errors. Data may look missing. |
| **Latency on key journey** | p95 latency of those routes > 1 s | The dashboard spins; logging a session feels stuck. People give up. |

Both alerts notify the **on-call agent** ([`oncall/`](oncall/README.md)) via webhook. A human
(the lead) owns the outcome.

### Key journey 5xx
Alert `LearnLoop key journey 5xx`. Users can't log sessions or load the dashboard. Treat it as
an outage of the core feature: triage below, and roll back first if the cause isn't clear
within about 15 minutes.

### Key journey latency
Alert `LearnLoop key journey latency`. Requests succeed but are slow. Look for slow
SQLAlchemy spans in Tempo (missing index, N+1 query) or a struggling database. If it started
right after a deploy, roll back.

## 1. Triage (first 5 minutes)

1. **Confirm the impact:** open Grafana at http://localhost:3001 (admin/admin) and the
   **LearnLoop** dashboard. Check request rate, 5xx ratio and p95 per route.
   - Is it one route or all? If `/health` is failing too, the app or database is down. If
     only one route fails, it's a code path.
   - Did it start right after a deploy? Compare with the deploy time in GitHub Actions →
     *Project-1 CI/CD*.
2. **Error logs:** Grafana → Explore → **Loki**:
   ```logql
   {service_name="learnloop"} | severity_text=~"(?i)error|critical"
   ```
   The JSON logs on stdout (`docker compose logs app`) carry the same `trace_id`:
   ```bash
   docker compose logs app | grep '"level": "error"'
   ```
   In Loki, the structured-metadata form of the query is
   `{service_name="learnloop"} | json | level="error"`, which works when the stdout logs
   are shipped.
3. **Traces:** Explore → **Tempo** → TraceQL
   `{ resource.service.name = "learnloop" && status = error }`. Open a trace to see which
   span failed (FastAPI handler or SQLAlchemy query), the `exception` event and its stack
   trace. Use **Logs for this span** to jump back to Loki.
4. **Metrics in Prometheus** (http://localhost:9090):
   ```promql
   sum by (http_route, http_status_code) (increase(learnloop_http_requests_total{http_status_code=~"5.."}[5m]))
   histogram_quantile(0.95, sum by (le, http_route) (rate(learnloop_http_request_duration_seconds_bucket[5m])))
   ```

## 2. Common causes

| Symptom | Likely cause | Where |
|---|---|---|
| 500 on `/api/dashboard` only, `ZeroDivisionError` | Progress/percentage maths not guarding zero (for example a track with no modules) | `backend/src/learnloop/logic.py` |
| 500 on every route, `OperationalError` / connection refused | Database down, wrong `DATABASE_URL`, connection pool exhausted | DB service, Render/Neon status |
| 500 after deploy, `UndefinedColumn` / `no such column` | Schema changed without migration | `models.py` |
| p95 > 1 s, slow SQLAlchemy spans | Missing index or N+1 query in the dashboard | `routes/dashboard.py` |
| 401 spikes (not paged) | Wrong `WRITE_TOKEN` in the client | Settings page / env |

## 3. Fix, verify, roll back

- **Code bug:** the on-call agent writes a failing unit test, fixes the code, and runs
  `cd backend && uv run pytest -q`. With `ONCALL_GIT=1` it also opens a `type:bug` issue and
  a PR (`Closes #n`). The PR goes through normal CI → dev → manual prod promotion
  ([`docs/process.md`](../docs/process.md)).
- **Verify:** rebuild or redeploy, generate a little traffic, and watch the 5xx ratio drop
  and the alert go back to **Normal**. The responder then marks the incident `resolved`.
- **Can't fix quickly? Roll back first, fix after.** Redeploy the previous good image; see
  [`rollback.md`](rollback.md). Rolling back is always acceptable when users are affected.
- **Write it up:** every incident folder in [`incidents/`](incidents/) has an `incident.md`
  (symptom, root cause, fix, test, follow-ups).

## Demo: alert → on-call agent → fix

Prerequisites: Docker Desktop, `uv`, Python 3.11+. The `claude` CLI is optional; without it a
stub agent escalates instead. Run all commands from `Project-1/`.

```bash
# 1. Start the whole stack (app + Postgres + OTel collector + Prometheus + Loki + Tempo + Grafana)
docker compose up --build -d

# 2. Start the on-call responder on the host (separate terminal)
cd ops/oncall && uv sync && uv run uvicorn responder:app --host 0.0.0.0 --port 8001
#    optional: export ONCALL_GIT=1 so the agent opens an issue + PR

# 3. Ship a "bad deploy": break the dashboard for tracks without modules
python ops/chaos/inject_bug.py
docker compose up --build -d app

# 4. Drive users through the key journey (creates a track with no modules)
python ops/chaos/traffic.py -n 120 --delay 0.5

# 5. In about 1-2 minutes, the "5xx on key journey" alert fires (Grafana → Alerting).
#    The responder logs "[oncall] accepted ..." and the agent starts.
curl http://localhost:8001/incidents

# 6. The agent adds a failing test, fixes logic.py and runs `uv run pytest`.
#    Review the diff (git diff) or the PR it opened.

# 7. Deploy the fix and confirm recovery
docker compose up --build -d app
python ops/chaos/traffic.py -n 30
#    The alert returns to Normal, Grafana sends "resolved" and the incident is marked resolved.

# 8. Evidence: ops/incidents/<id>/ (alert.json, metric.json, logs.json, traces.json,
#    prompt.txt, agent-response.txt, resolved.json, incident.md)
```

To reset the demo without the agent, run `python ops/chaos/inject_bug.py --revert`, then
`docker compose up --build -d app`.
