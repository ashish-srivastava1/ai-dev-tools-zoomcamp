# AGENTS.md — LearnLoop

Entry point for AI coding agents working in `Project-1/`. Keep this file
short. The details live in the modular docs linked below; read the ones
relevant to your task before you change anything.

## What this is
LearnLoop is a single-user learning dashboard (tracks, modules, study
sessions, progress dashboard). The source of truth for behaviour is
[`product-spec.md`](product-spec.md).

## Read before working
| Doc | Read when |
|---|---|
| [`product-spec.md`](product-spec.md) | Always — features, acceptance criteria, NFRs |
| [`docs/process.md`](docs/process.md) | Always — the issue → branch → PR workflow and the definition of done |
| [`docs/agent-team.md`](docs/agent-team.md) | To find out which role you are playing and what you hand off |
| [`docs/architecture.md`](docs/architecture.md) | Before touching code, infra or CI |
| [`docs/backlog.md`](docs/backlog.md) | Seed list of the issues in the GitHub tracker |
| [`docs/deployment.md`](docs/deployment.md) | Before touching CI/CD, Render or environments |
| [`ops/README.md`](ops/README.md) | Observability, alerts, on-call agent, runbook, rollback |
| [`.claude/agents/`](.claude/agents/) | Role prompts for each agent in the team |

## Hard rules
1. **Work from an issue.** Every change belongs to a GitHub issue. Reference it in the branch name (`feat/8-sessions-api`), the commits (`#8`) and the PR (`Closes #8`). Issue numbers are listed in `docs/backlog.md`; the tracker is https://github.com/users/ashish-srivastava1/projects/1. Comment on the issue when you start and when you finish.
2. **The spec wins.** If a request conflicts with `product-spec.md`, stop and flag it on the issue. Don't silently deviate.
3. **Contract first.** API changes start in `openapi.yaml`. The backend implements the contract, and the frontend calls it only through `frontend/src/api/client.js`.
4. **Test first.** Write or adjust the tests before the implementation. The full suite (`./scripts/test.sh` or `.\scripts\test.ps1`) must pass before you open a PR.
5. **No PII or secrets in telemetry or logs.** Never log session topics, notes, tokens or the DB URL.
6. **Python:** use `uv` only, never bare `pip`. **Node:** use `npm`.
7. Stay inside `Project-1/`. Don't edit the homework folders.

## Commands
Run everything from `Project-1/`.

```bash
# whole system: app + Postgres + OTel Collector + Prometheus + Loki + Tempo + Grafana
docker compose up --build            # app http://localhost:8000, Grafana http://localhost:3001

# whole test suite in containers (backend lint + unit + integration on Postgres + frontend)
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from tests
#   wrappers: ./scripts/test.sh | .\scripts\test.ps1 | make test

# backend (uv)
cd backend && uv run uvicorn learnloop.main:app --reload --port 8000
cd backend && uv run pytest                      # unit (SQLite)
cd backend && INTEGRATION_DATABASE_URL=postgresql+psycopg://learnloop:learnloop@localhost:5432/learnloop uv run pytest -m integration
cd backend && uv run ruff check . && uv run ruff format --check .

# frontend (npm)
cd frontend && npm install && npm run dev        # http://localhost:5173, proxies /api to :8000
cd frontend && npm run lint && npm test && npm run build

# contract
npx @redocly/cli@1 lint openapi.yaml

# on-call agent + chaos demo (see ops/runbook.md)
cd ops/oncall && uv run pytest -q
cd ops/oncall && uv run uvicorn responder:app --host 0.0.0.0 --port 8001
python ops/chaos/inject_bug.py [--status|--revert]
python ops/chaos/traffic.py -n 120 --delay 0.5
```
