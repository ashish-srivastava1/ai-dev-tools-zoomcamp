# Deployment (dev + production on Render)

## How a release flows
```
PR ──► CI: backend lint+unit · integration (Postgres) · frontend lint+test+build · OpenAPI lint · docker build
merge to main ──► same checks ──► publish ghcr.io/<owner>/learnloop:<sha> (+ :main)
              ──► deploy-dev   (automatic)      ──► smoke test DEV_URL
              ──► deploy-prod  (waits for MANUAL approval on the `production` environment)
                                                ──► smoke test PROD_URL
rollback ──► project-1-rollback workflow (any earlier <sha>) - see ops/rollback.md
```
Workflows: `.github/workflows/project-1-cicd.yml`, `.github/workflows/project-1-rollback.yml`.

Until the secrets and variables below exist, the deploy jobs **skip with a warning** in the
run summary. CI and image publishing still work.

## One-time setup

All commands are for PowerShell with `gh` logged in (`gh auth status`), run from the repo root.

```powershell
$Repo = "ashish-srivastava1/ai-dev-tools-zoomcamp"
```

### 1. Container image access (GHCR)
The first push to `main` publishes `ghcr.io/ashish-srivastava1/learnloop`. Then do one of:
- **Make it public** (simplest): GitHub → your profile → *Packages* → `learnloop` → *Package settings* → *Change visibility* → Public.
- **Or keep it private:** in Render, add a registry credential (*Settings → Registry Credentials*) for `ghcr.io`, with username = your GitHub user and password = a classic PAT with `read:packages`.

### 2. Databases (one per environment)
- **Recommended: Neon free tier.** Create a project `learnloop` with two branches, `dev` and `prod` (or two projects). Copy each connection string.
- **Alternative:** Render PostgreSQL (note that the free instance expires after 30 days).

`postgres://...` or `postgresql://...` URLs are fine; the app rewrites them to the psycopg 3 driver.
Keep `?sslmode=require` if the provider includes it.

### 3. Render web services (deploy an existing image)
Create **two** services: Render → *New* → *Web Service* → *Existing image*:

| Setting | learnloop-dev | learnloop-prod |
|---|---|---|
| Image URL | `ghcr.io/ashish-srivastava1/learnloop:main` | `ghcr.io/ashish-srivastava1/learnloop:main` |
| Health check path | `/health` | `/health` |
| `DATABASE_URL` | Neon `dev` string | Neon `prod` string |
| `APP_ENV` | `dev` | `prod` |
| `WRITE_TOKEN` | optional | **set a long random value** (writes then need it; enter it in the app's Settings page) |
| `TELEMETRY_EXPORTER` | `none` (or `otlp`, see below) | `none` (or `otlp`) |

Render injects `PORT`; the image listens on it.

**Telemetry in the cloud (optional).** The backend exports OTLP over **gRPC**. To send to Grafana
Cloud, set `TELEMETRY_EXPORTER=otlp`, `OTEL_EXPORTER_OTLP_ENDPOINT=<your stack's OTLP endpoint>` and
`OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic <base64 instanceId:token>`. Grafana Cloud's
documented OTLP gateway is **HTTP/protobuf**, so the gRPC exporter may not connect directly. If it
doesn't, either run an OpenTelemetry Collector in between, or keep `none` in the cloud and
demonstrate observability with the local docker compose stack (Grafana at http://localhost:3001).

### 4. Deploy hooks → GitHub secrets, URLs → variables
For each Render service: *Settings → Deploy Hook* → copy the URL (`https://api.render.com/deploy/srv-...?key=...`).
CD calls it as `<hook>&imgURL=<url-encoded ghcr image:sha>`. Render's deploy hook for
image-backed services accepts `imgURL`, so every deploy pins an exact commit image.

```powershell
gh secret set RENDER_DEPLOY_HOOK_DEV  --repo $Repo --body "https://api.render.com/deploy/srv-XXXX?key=YYYY"
gh secret set RENDER_DEPLOY_HOOK_PROD --repo $Repo --body "https://api.render.com/deploy/srv-AAAA?key=BBBB"
gh variable set DEV_URL  --repo $Repo --body "https://learnloop-dev.onrender.com"
gh variable set PROD_URL --repo $Repo --body "https://learnloop-prod.onrender.com"
```

### 5. GitHub environments (manual production gate)
```powershell
# dev: no protection
gh api -X PUT "repos/$Repo/environments/dev" | Out-Null

# production: you must approve every deploy/rollback
$me = gh api user --jq .id
@"
{ "reviewers": [ { "type": "User", "id": $me } ], "deployment_branch_policy": null }
"@ | gh api -X PUT "repos/$Repo/environments/production" --input - | Out-Null
```
Or use *Settings → Environments → New environment → production → Required reviewers*.
(Required reviewers on a **public** repo are available on the free plan.)

### 6. Protect `main`
```powershell
@"
{
  "required_status_checks": { "strict": true, "contexts": [
    "backend (lint + unit tests)", "integration tests (PostgreSQL)",
    "frontend (lint + tests + build)", "OpenAPI contract lint" ] },
  "enforce_admins": false,
  "required_pull_request_reviews": null,
  "restrictions": null
}
"@ | gh api -X PUT "repos/$Repo/branches/main/protection" --input -
```
Required checks only gate PRs that touch `Project-1/**`. PRs for the homework folders don't run
this workflow, so if they get blocked, drop the checks from protection or use a ruleset scoped to the
`Project-1` paths.

## Promote and roll back
- **Promote to production:** open the latest **project-1-cicd** run on `main` → *Review deployments* → tick `production` → *Approve and deploy*.
- **Roll back:** `gh workflow run project-1-rollback.yml -f environment=production -f sha=<good-sha>`. Details are in [`ops/rollback.md`](../ops/rollback.md).

## Checklist
- [ ] GHCR package public (or Render registry credential added)
- [ ] Two databases created
- [ ] `learnloop-dev` and `learnloop-prod` Render services created from the image
- [ ] Secrets `RENDER_DEPLOY_HOOK_DEV`, `RENDER_DEPLOY_HOOK_PROD`
- [ ] Variables `DEV_URL`, `PROD_URL`
- [ ] Environments `dev` and `production` (production has a required reviewer)
- [ ] Branch protection on `main`
- [ ] Rollback drill done and evidence recorded in `ops/rollback.md`
