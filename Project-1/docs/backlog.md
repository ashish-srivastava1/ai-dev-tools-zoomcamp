# Seed backlog

These are now GitHub issues (board: https://github.com/users/ashish-srivastava1/projects/1) (label `project-1`). The acceptance-criteria IDs
refer to `product-spec.md`. Issues are listed in rough dependency order.

| # | Issue | Title | Type / Area | Acceptance criteria |
|---|---|---|---|---|
| 1 | [#4](https://github.com/ashish-srivastava1/ai-dev-tools-zoomcamp/issues/4) | Write OpenAPI contract for tracks, modules, sessions, dashboard, settings | docs / backend | The contract covers F1–F5; it validates with an OpenAPI linter; errors use the `{detail}` shape |
| 2 | [#5](https://github.com/ashish-srivastava1/ai-dev-tools-zoomcamp/issues/5) | Backend skeleton: FastAPI app, config, Postgres via SQLAlchemy, `/health` | feature / backend, db | `/health` returns ok; the DB URL comes from env; tables are created on startup or by migration |
| 3 | [#6](https://github.com/ashish-srivastava1/ai-dev-tools-zoomcamp/issues/6) | Tracks API (F1) | feature / backend | AC1.1–AC1.4 covered by tests |
| 4 | [#7](https://github.com/ashish-srivastava1/ai-dev-tools-zoomcamp/issues/7) | Modules API (F2) | feature / backend | AC2.1–AC2.3 covered by tests |
| 5 | [#8](https://github.com/ashish-srivastava1/ai-dev-tools-zoomcamp/issues/8) | Sessions API (F3) | feature / backend | AC3.1–AC3.4 covered by tests, including timezone-aware date validation |
| 6 | [#9](https://github.com/ashish-srivastava1/ai-dev-tools-zoomcamp/issues/9) | Dashboard API (F4) incl. streak and week logic | feature / backend | AC4.1–AC4.6; tests for month and year boundaries and timezones |
| 7 | [#10](https://github.com/ashish-srivastava1/ai-dev-tools-zoomcamp/issues/10) | Settings API (F5) + write-token guard | feature / backend | AC5.1; mutating endpoints return 401 without a token when `WRITE_TOKEN` is set |
| 8 | [#11](https://github.com/ashish-srivastava1/ai-dev-tools-zoomcamp/issues/11) | Frontend skeleton: Vite app, routing, `api/client.js` | feature / frontend | All calls go through the client; the API base URL comes from env |
| 9 | [#12](https://github.com/ashish-srivastava1/ai-dev-tools-zoomcamp/issues/12) | Tracks and modules UI | feature / frontend | AC1.x and AC2.x reachable from the UI; component tests |
| 10 | [#13](https://github.com/ashish-srivastava1/ai-dev-tools-zoomcamp/issues/13) | Log-session form and session list UI | feature / frontend | AC3.1–AC3.4; validation errors shown; component tests |
| 11 | [#14](https://github.com/ashish-srivastava1/ai-dev-tools-zoomcamp/issues/14) | Dashboard UI (cards, per-track bars, 8-week chart, recent) | feature / frontend | AC4.1–AC4.6; empty state; component tests |
| 12 | [#15](https://github.com/ashish-srivastava1/ai-dev-tools-zoomcamp/issues/15) | Settings UI | feature / frontend | AC5.1 |
| 13 | [#16](https://github.com/ashish-srivastava1/ai-dev-tools-zoomcamp/issues/16) | Integration tests against Compose Postgres | test / backend | Covers the key journey end to end; separate from the unit tests; `make test` runs everything |
| 14 | [#17](https://github.com/ashish-srivastava1/ai-dev-tools-zoomcamp/issues/17) | Dockerfile + docker-compose (app + db) | infra / ci | `docker compose up` gives a working app at :8000 |
| 15 | [#18](https://github.com/ashish-srivastava1/ai-dev-tools-zoomcamp/issues/18) | CI: PR checks (lint, unit, frontend, integration) | infra / ci | Runs on every PR touching `Project-1/**` |
| 16 | [#19](https://github.com/ashish-srivastava1/ai-dev-tools-zoomcamp/issues/19) | CD: deploy to dev on merge, smoke test, manual prod promotion, rollback doc | infra / ci | Dev URL live; prod needs approval; `ops/rollback.md` tested once |
| 17 | [#20](https://github.com/ashish-srivastava1/ai-dev-tools-zoomcamp/issues/20) | Telemetry: traces, metrics, JSON logs with trace_id on the key journey; no PII | feature / ops | A single request is traceable across all three signals in Grafana |
| 18 | [#21](https://github.com/ashish-srivastava1/ai-dev-tools-zoomcamp/issues/21) | Observability stack in Compose + dashboard | infra / ops | Grafana shows the request rate, errors and p95 for the key journey |
| 19 | [#22](https://github.com/ashish-srivastava1/ai-dev-tools-zoomcamp/issues/22) | User-impact alert rules (5xx rate, p95) | infra / ops | The alert fires on injected 5xx errors and resolves afterwards |
| 20 | [#23](https://github.com/ashish-srivastava1/ai-dev-tools-zoomcamp/issues/23) | On-call agent: webhook → diagnose → issue + fix PR | feature / ops | Demo: an injected bug triggers the alert, then the agent opens a fix PR; incident note in `ops/incidents/` |
| 21 | [#24](https://github.com/ashish-srivastava1/ai-dev-tools-zoomcamp/issues/24) | Agent role prompts in `.claude/agents/` + agent-team doc links | docs | One file per role; referenced from `docs/agent-team.md` |
| 22 | [#25](https://github.com/ashish-srivastava1/ai-dev-tools-zoomcamp/issues/25) | README: setup, run, test, deploy, demo URL, screenshots | docs | A reviewer can run everything from the README alone |
