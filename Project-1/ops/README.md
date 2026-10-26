# ops/: production readiness

| Path | What | Owner role |
|---|---|---|
| [`observability/`](observability/) | OTel Collector, Prometheus, Loki, Tempo, Grafana (datasources, dashboard, alert rules, contact point) used by `docker compose` | DevOps agent |
| [`oncall/`](oncall/README.md) | On-call responder: Grafana webhook → evidence → headless coding agent → fix (+ issue/PR) | On-call agent |
| [`chaos/`](chaos/) | `inject_bug.py` (break the key journey on purpose) and `traffic.py` (drive the journey) for the demo | On-call agent |
| [`runbook.md`](runbook.md) | What each alert means, where to look, common causes, fix / verify / roll back, demo script | On-call agent |
| [`rollback.md`](rollback.md) | How to roll dev or prod back to a previous image | DevOps / CI-CD agent |
| [`incidents/`](incidents/) | One folder per incident handled by the on-call agent (evidence + `incident.md`) | On-call agent |

Alerting fires on **user impact** for the key journey (5xx ratio and p95 latency of
`POST /api/sessions` and `GET /api/dashboard`), never on CPU or memory graphs.
