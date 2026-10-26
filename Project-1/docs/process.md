# Development process

## Flow
```
spec (product-spec.md)
  → issue in GitHub tracker (user story + acceptance criteria + labels)
  → branch  feat/<issue#>-<slug>
  → tests first, then implementation
  → PR "Closes #<n>"  →  CI (lint, unit, frontend, integration)
  → review (Reviewer agent + human)  →  merge to main
  → CD: auto-deploy to dev → smoke test → manual approval → prod
```

## Task tracker
- **Where:** GitHub Issues + a GitHub Projects board on the public repo
  `ashish-srivastava1/ai-dev-tools-zoomcamp`, using the label `project-1`.
- **Board:** GitHub Projects "LearnLoop - Final Project" (public), Status: Todo → In Progress → Done. Seeded by `scripts/create-issues.ps1`.
- **Every issue has:** a user story, acceptance criteria as a checklist
  (tied to spec IDs such as AC3.2), a `type:` label
  (feature/test/infra/docs/bug), and an `area:` label
  (frontend/backend/db/ci/ops).
- **Evidence that agents used it:** agents comment on the issue at start and
  finish, the PR links the issue, and acceptance-criteria boxes are ticked
  in the PR description.

## Definition of done
- [ ] All acceptance criteria on the issue are met and ticked
- [ ] Tests added or updated, and `make test` passes locally and in CI
- [ ] `openapi.yaml` updated if the API changed
- [ ] Docs updated (README / AGENTS.md / docs) if behaviour or commands changed
- [ ] No secrets or PII in code, logs or telemetry
- [ ] PR reviewed and merged, and the issue is closed automatically

## Branching and environments
- `main` is always deployable. Every merge auto-deploys to **dev**.
- **prod** is promoted manually through a GitHub Actions environment with
  required approval. Rollback means redeploying the previous image tag (see `ops/rollback.md`).
