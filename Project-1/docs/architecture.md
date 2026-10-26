# Architecture (proposed)

## Stack
| Layer | Choice | Why |
|---|---|---|
| Frontend | React 19 + Vite, react-router, Vitest + Testing Library | Same as HW2/HW3; fast tests |
| API contract | OpenAPI 3.1 (`openapi.yaml`) | Contract-first; drives backend and client |
| Backend | FastAPI + SQLAlchemy 2, `uv`, pytest | Proven in HW3 |
| Database | PostgreSQL 16 (SQLite allowed only for quick unit tests) | Persistent, same engine locally and in the cloud |
| Container | One image: FastAPI serves the API and the built frontend; Docker Compose adds Postgres and the observability stack | Single-command run |
| Observability | OpenTelemetry SDK → OTel Collector → Prometheus (metrics), Tempo (traces), Loki (logs) → Grafana | Reuses HW4 |
| Alerting | Grafana alert rules → webhook contact point | Alerts on user impact |
| On-call agent | Webhook receiver service + headless coding agent (adapted from the HW4 responder) | Wakes on an alert and opens a fix PR |
| CI/CD | GitHub Actions: PR checks → build and push image (GHCR) → deploy to dev → manual approval → prod | Worth 3 points |
| Hosting | Render web services (dev + prod); managed Postgres per environment (Render or Neon) | Used in HW3 |

## Runtime view
```
Browser ──► FastAPI (/api/*, static UI) ──► PostgreSQL
               │  OTel SDK (traces, metrics, JSON logs with trace_id)
               ▼
         OTel Collector ──► Prometheus / Tempo / Loki ──► Grafana
                                                         │ alert (5xx rate / p95)
                                                         ▼
                                              On-call agent (webhook)
                                                         │ diagnose → GitHub issue + fix PR
```

## Environments
| Env | How it's deployed | Database | Telemetry |
|---|---|---|---|
| local | `docker compose up` | Compose Postgres | Local Grafana stack |
| dev | Auto on merge to `main` | dev DB | Grafana Cloud (free) or OTLP endpoint |
| prod | Manual approval in GitHub Actions | prod DB | Same, tagged `env=prod` |

Configuration comes only from environment variables (`DATABASE_URL`, `WRITE_TOKEN`, `OTEL_*`, `APP_ENV`).

## Open decisions
- Managed Postgres: one Render DB per env, or Neon with dev/prod branches.
- Deployed telemetry backend: Grafana Cloud free tier, or a demo that runs locally only.
