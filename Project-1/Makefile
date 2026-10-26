# LearnLoop - convenience targets (Linux/macOS/WSL). On Windows use scripts\test.ps1
# or the docker compose commands shown in README.md.

COMPOSE_TEST = docker compose -f docker-compose.test.yml
PG_URL ?= postgresql+psycopg://learnloop:learnloop@localhost:5432/learnloop

.PHONY: dev up down logs test test-unit test-integration test-frontend lint

dev:            ## backend (:8000) + Vite dev server (:5173) without Docker
	cd backend && uv run uvicorn learnloop.main:app --reload --port 8000 & \
	cd frontend && npm run dev

up:             ## full stack: db + app + observability
	docker compose up --build -d --wait

down:
	docker compose down

logs:
	docker compose logs -f app

test:           ## THE single test command: everything, in containers
	$(COMPOSE_TEST) up --build --abort-on-container-exit --exit-code-from tests; \
	status=$$?; $(COMPOSE_TEST) down -v >/dev/null 2>&1; exit $$status

test-unit:
	cd backend && uv run pytest -q

test-integration: ## needs Postgres, e.g. `docker compose up -d db`
	cd backend && INTEGRATION_DATABASE_URL=$(PG_URL) uv run pytest -q -m integration

test-frontend:
	cd frontend && npm test

lint:
	cd backend && uv run ruff check . && uv run ruff format --check .
	cd frontend && npm run lint
