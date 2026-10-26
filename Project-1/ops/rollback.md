# Rollback runbook

Every merge to `main` publishes an image `ghcr.io/ashish-srivastava1/learnloop:<full-commit-sha>`
(plus the moving tag `main`). Rolling back means **redeploying an older, known-good image**.
No rebuild is needed.

## When to roll back
- A user-impact alert fires right after a deploy (5xx rate or p95 latency on
  `POST /api/sessions` / `GET /api/dashboard`). See `ops/` alert rules.
- The CD smoke test fails on dev or production.
- A fix will take longer than about 15 minutes. Roll back first, then fix forward.

## Option 1: rollback workflow (preferred)
1. Find the last good SHA. Use one of:
   - GitHub → *Actions* → **project-1-cicd** → the last green run that deployed to the environment (the job summary shows the commit).
   - GitHub → profile → *Packages* → **learnloop** → tags.
   - `gh run list --workflow project-1-cicd.yml --branch main --status success --limit 5 --json headSha,displayTitle`
2. Run it:
   ```powershell
   gh workflow run project-1-rollback.yml -f environment=production -f sha=<full-sha>
   gh run watch
   ```
   Or use *Actions* → **project-1-rollback** → *Run workflow*.
3. A production rollback waits for approval on the `production` environment. Approve it in the run page.
4. The workflow checks that the tag exists in GHCR, triggers the Render deploy hook with that image, and smoke-tests `/health` and `/api/dashboard`.

## Option 2: Render dashboard
Render → service `learnloop-prod` (or `learnloop-dev`) → *Events* → pick an earlier successful deploy → **Rollback**.
This is quickest if GitHub Actions is unavailable. The next CD run will deploy `main` again, so fix `main` before merging anything else.

## Option 3: git revert + normal pipeline
```powershell
git revert <bad-commit-sha>
git push origin HEAD:revert-<short-sha>   # open a PR; CI runs; merge
```
The merge deploys to dev automatically, then to production after approval. This is the slowest option, but it leaves `main` correct.

## Database note
The schema is created **additively** by SQLAlchemy `create_all()` at startup (new tables/columns
only, no destructive migrations). An older image runs fine against a newer database, so rolling
back the image is safe. If a future change adds a destructive migration, it must ship with an
explicit down-migration and this note must be updated.

## Rollback drill (do once, keep the evidence)
- [ ] Deploy two consecutive commits to dev (A then B). Note both SHAs.
- [ ] Run `project-1-rollback` with `environment=dev`, `sha=A`.
- [ ] Confirm the job summary shows image `...:A` and the smoke test passed.
- [ ] Confirm the dev URL still serves data (same tracks and sessions as before).
- [ ] Redeploy B (re-run the CD run, or run the rollback workflow with `sha=B`).

Evidence (paste run links and screenshots here):

| Date | Env | From SHA | To SHA | Run link | Result |
|---|---|---|---|---|---|
|  |  |  |  |  |  |
