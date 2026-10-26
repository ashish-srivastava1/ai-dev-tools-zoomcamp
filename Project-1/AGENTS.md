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

## Hard rules
1. **Work from an issue.** Every change belongs to a GitHub issue. Reference it in the branch name (`feat/8-sessions-api`), the commits (`#8`) and the PR (`Closes #8`). Issue numbers are listed in `docs/backlog.md`; the tracker is https://github.com/users/ashish-srivastava1/projects/1. Comment on the issue when you start and when you finish.
2. **The spec wins.** If a request conflicts with `product-spec.md`, stop and flag it on the issue. Don't silently deviate.
3. **Contract first.** API changes start in `openapi.yaml`. The backend implements the contract, and the frontend calls it only through `frontend/src/api/client.js`.
4. **Test first.** Write or adjust the tests before the implementation. `make test` must pass before you open a PR.
5. **No PII or secrets in telemetry or logs.** Never log session topics, notes, tokens or the DB URL.
6. **Python:** use `uv` only, never bare `pip`. **Node:** use `npm`.
7. Stay inside `Project-1/`. Don't edit the homework folders.

## Commands
To be filled in as each part lands (`make dev`, `make test`, `docker compose up`).
