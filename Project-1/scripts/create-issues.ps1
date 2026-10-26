<#
.SYNOPSIS
  Seeds the LearnLoop (Project-1) backlog into GitHub Issues and a public
  GitHub Projects board, from docs/backlog.md.

.USAGE
  # one-time: install GitHub CLI and log in with the 'project' scope
  winget install --id GitHub.cli
  gh auth login
  gh auth refresh -s project

  # from the repo root (or anywhere inside the repo)
  powershell -ExecutionPolicy Bypass -File .\Project-1\scripts\create-issues.ps1

  Safe to re-run: labels are upserted, and issues whose exact title already
  exists are skipped (but still added to the board).
#>

$ErrorActionPreference = 'Stop'
$Repo  = 'ashish-srivastava1/ai-dev-tools-zoomcamp'
$Owner = 'ashish-srivastava1'
$ProjectTitle = 'LearnLoop - Final Project'

# ---------- pre-checks ----------
gh auth status | Out-Null
$vis = (gh repo view $Repo --json visibility | ConvertFrom-Json).visibility
if ($vis -ne 'PUBLIC') {
  Write-Warning "Repo $Repo is $vis. The rubric needs a PUBLIC tracker. Make it public: gh repo edit $Repo --visibility public --accept-visibility-change-consequences"
}

# ---------- labels ----------
$labels = @(
  @{n='project-1';      c='5319e7'; d='LearnLoop final project'},
  @{n='type:feature';   c='0e8a16'; d='New functionality'},
  @{n='type:test';      c='fbca04'; d='Tests'},
  @{n='type:infra';     c='1d76db'; d='Docker / CI / CD / hosting'},
  @{n='type:docs';      c='c5def5'; d='Documentation'},
  @{n='type:bug';       c='d73a4a'; d='Something is broken'},
  @{n='area:backend';   c='bfdadc'; d='FastAPI backend'},
  @{n='area:frontend';  c='bfdadc'; d='React frontend'},
  @{n='area:db';        c='bfdadc'; d='Database'},
  @{n='area:ci';        c='bfdadc'; d='CI/CD'},
  @{n='area:ops';       c='bfdadc'; d='Observability / alerting / on-call'}
)
foreach ($l in $labels) {
  gh label create $l.n --repo $Repo --color $l.c --description $l.d --force | Out-Null
}
Write-Host "Labels ready."

# ---------- issues ----------
# Each body: user story, spec refs, acceptance criteria checklist.
$issues = @(
@{ t='[P1-01] OpenAPI contract for tracks, modules, sessions, dashboard, settings'; l='type:docs,area:backend'; b=@'
**Story:** As an agent building the backend or frontend, I want one API contract so both sides agree before code is written.

**Spec:** product-spec.md F1-F5

**Acceptance criteria**
- [ ] `Project-1/openapi.yaml` covers every F1-F5 operation (CRUD tracks, modules, sessions; GET dashboard; GET/PUT settings; GET /health)
- [ ] Request/response schemas match section 3 of the spec, including validation limits
- [ ] Errors use `{ "detail": ... }`; 401/404/422 documented
- [ ] Spec passes an OpenAPI linter (e.g. `npx @redocly/cli lint`)
'@ },
@{ t='[P1-02] Backend skeleton: FastAPI, config, Postgres via SQLAlchemy, /health'; l='type:feature,area:backend,area:db'; b=@'
**Story:** As a developer, I want a running backend skeleton so feature endpoints can be added test-first.

**Acceptance criteria**
- [ ] `uv` project under `Project-1/backend`, FastAPI app factory
- [ ] `DATABASE_URL` read from env; Postgres in compose, SQLite allowed for fast unit tests
- [ ] Tables created on startup (or migration) for Track, Module, Session, Settings
- [ ] `GET /health` returns `{"status":"ok"}`; pytest smoke test passes
'@ },
@{ t='[P1-03] Tracks API (F1)'; l='type:feature,area:backend'; b=@'
**Story:** As a learner, I want to create, edit and archive learning tracks.

**Spec:** AC1.1-AC1.4

**Acceptance criteria**
- [ ] AC1.1 create + list
- [ ] AC1.2 duplicate name (case-insensitive) or target <= 0 returns 422
- [ ] AC1.3 edit name/description/target/colour
- [ ] AC1.4 archive hides from dashboard and session form, keeps sessions
- [ ] Unit tests for each AC
'@ },
@{ t='[P1-04] Modules API (F2)'; l='type:feature,area:backend'; b=@'
**Story:** As a learner, I want to break a track into modules and mark progress.

**Spec:** AC2.1-AC2.3

**Acceptance criteria**
- [ ] AC2.1 add modules, listed by position
- [ ] AC2.2 status change; completion % = done/total rounded, 0 when none
- [ ] AC2.3 reorder and delete; deleted module's sessions keep module_id = null
- [ ] Unit tests for each AC
'@ },
@{ t='[P1-05] Sessions API (F3) - key user journey'; l='type:feature,area:backend'; b=@'
**Story:** As a learner, I want to log study sessions so my progress is tracked.

**Spec:** AC3.1-AC3.4

**Acceptance criteria**
- [ ] AC3.1 create session (date, minutes, track, optional module, topic, notes)
- [ ] AC3.2 validation: minutes 1-600, date not in future in user timezone, track exists and not archived, module belongs to track -> 422
- [ ] AC3.3 edit and delete
- [ ] AC3.4 list filtered by track and date range, newest first, 20 per page
- [ ] Unit tests for each AC, including timezone edge case
'@ },
@{ t='[P1-06] Dashboard API (F4) incl. streak and week logic'; l='type:feature,area:backend'; b=@'
**Story:** As a learner, I want a single dashboard call that summarises my progress.

**Spec:** AC4.1-AC4.6

**Acceptance criteria**
- [ ] AC4.1 this-week hours vs weekly goal (week_start, user timezone)
- [ ] AC4.2 current and longest streak, correct across month/year boundaries and timezones
- [ ] AC4.3 per-track hours vs target and module completion %
- [ ] AC4.4 last 8 weeks including zero weeks
- [ ] AC4.5 5 most recent sessions
- [ ] AC4.6 empty-state flag when there is no data
- [ ] Pure functions for week/streak math with unit tests (boundary dates: 31 Dec -> 1 Jan, 28/29 Feb)
'@ },
@{ t='[P1-07] Settings API (F5) + write-token guard'; l='type:feature,area:backend'; b=@'
**Story:** As the owner, I want to set my goal and timezone, and protect writes on the public demo.

**Spec:** AC5.1, NFR Security

**Acceptance criteria**
- [ ] GET/PUT settings (weekly_goal_hours, timezone validated as IANA, week_start)
- [ ] When `WRITE_TOKEN` is set, POST/PUT/PATCH/DELETE without `Authorization: Bearer <token>` return 401
- [ ] Token never logged
- [ ] Unit tests
'@ },
@{ t='[P1-08] Frontend skeleton: Vite, routing, api/client.js'; l='type:feature,area:frontend'; b=@'
**Story:** As a developer, I want a frontend skeleton where all backend calls go through one client.

**Acceptance criteria**
- [ ] Vite + React under `Project-1/frontend`, routes: Dashboard, Tracks, Sessions, Settings
- [ ] `src/api/client.js` is the only module calling fetch; base URL from `VITE_API_BASE_URL` (same-origin in container)
- [ ] Vitest + Testing Library set up with one passing test
'@ },
@{ t='[P1-09] Tracks and modules UI'; l='type:feature,area:frontend'; b=@'
**Story:** As a learner, I want to manage tracks and modules in the browser.

**Spec:** AC1.x, AC2.x

**Acceptance criteria**
- [ ] Create/edit/archive track forms with validation messages from API
- [ ] Module list per track: add, status toggle, reorder, delete
- [ ] Component tests
'@ },
@{ t='[P1-10] Log-session form and session list UI'; l='type:feature,area:frontend'; b=@'
**Story:** As a learner, I want a quick form to log a session and see past sessions.

**Spec:** AC3.1-AC3.4

**Acceptance criteria**
- [ ] Form with date (default today), minutes, track, module (filtered by track), topic, notes
- [ ] API 422 errors shown next to fields
- [ ] After save, dashboard reflects the session without manual refresh
- [ ] Session list with track/date filters, pagination, edit, delete
- [ ] Component tests
'@ },
@{ t='[P1-11] Dashboard UI'; l='type:feature,area:frontend'; b=@'
**Story:** As a learner, I want to see my progress at a glance.

**Spec:** AC4.1-AC4.6

**Acceptance criteria**
- [ ] Cards: this week vs goal (progress bar), current and longest streak
- [ ] Per-track hours vs target bars and completion %
- [ ] 8-week bar chart
- [ ] Recent 5 sessions
- [ ] Empty state prompting to create a track
- [ ] Component tests
'@ },
@{ t='[P1-12] Settings UI'; l='type:feature,area:frontend'; b=@'
**Story:** As a learner, I want to change my weekly goal, timezone and week start.

**Spec:** AC5.1

**Acceptance criteria**
- [ ] Settings form; dashboard recalculates after save
- [ ] Optional write-token field stored in browser for the demo
- [ ] Component test
'@ },
@{ t='[P1-13] Integration tests against Postgres'; l='type:test,area:backend'; b=@'
**Story:** As a maintainer, I want end-to-end API tests against a real database.

**Acceptance criteria**
- [ ] Tests in `backend/tests/integration/`, separate from unit tests (pytest marker)
- [ ] Cover key journey: create track -> add module -> log session -> dashboard totals correct
- [ ] Run against compose Postgres (or testcontainers)
- [ ] `make test` runs backend unit + frontend + integration with one command
'@ },
@{ t='[P1-14] Dockerfile + docker-compose (app + db)'; l='type:infra,area:ci'; b=@'
**Story:** As a reviewer, I want to start the whole system with one command.

**Acceptance criteria**
- [ ] Multi-stage Dockerfile: builds frontend, FastAPI serves API + static UI
- [ ] `docker compose up --build` starts Postgres + app (healthchecks, depends_on)
- [ ] App reachable at http://localhost:8000, data persists across restarts
- [ ] README instructions
'@ },
@{ t='[P1-15] CI: PR checks'; l='type:infra,area:ci'; b=@'
**Story:** As a maintainer, I want every PR tested automatically.

**Acceptance criteria**
- [ ] `.github/workflows/project-1-ci.yml` at repo root, triggered on PRs touching `Project-1/**`
- [ ] Jobs: backend lint + unit, frontend lint + tests, integration tests with Postgres service
- [ ] Required status check on main
'@ },
@{ t='[P1-16] CD: deploy to dev on merge, manual prod promotion, rollback'; l='type:infra,area:ci'; b=@'
**Story:** As the owner, I want automatic dev deploys and a controlled prod release with a rollback path.

**Acceptance criteria**
- [ ] On merge to main: build and push image (GHCR, tagged with SHA), deploy to dev, run smoke test
- [ ] Prod deploy via GitHub environment `production` with required reviewer approval
- [ ] `ops/rollback.md`: redeploy previous SHA tag; rollback exercised once and evidence recorded
- [ ] Dev and prod public URLs in README
'@ },
@{ t='[P1-17] Telemetry on key journey: traces, metrics, JSON logs with trace_id'; l='type:feature,area:ops'; b=@'
**Story:** As an on-call engineer, I want to follow one request across metrics, traces and logs.

**Spec:** NFR Observability

**Acceptance criteria**
- [ ] OpenTelemetry SDK: FastAPI + SQLAlchemy instrumentation, OTLP export
- [ ] Metrics: request count by route/method/status, latency histogram; business counter `sessions_logged_total`
- [ ] Structured JSON logs include trace_id and span_id
- [ ] No topics, notes, tokens or DB URL in any signal (test asserts this)
'@ },
@{ t='[P1-18] Observability stack in compose + Grafana dashboard'; l='type:infra,area:ops'; b=@'
**Story:** As an on-call engineer, I want to see the key journey's health in a UI.

**Acceptance criteria**
- [ ] Compose profile adds OTel Collector, Prometheus, Tempo, Loki, Grafana (provisioned datasources)
- [ ] Dashboard: request rate, 5xx rate, p95 latency for POST /api/sessions and GET /api/dashboard
- [ ] Trace-to-logs link works from Tempo to Loki
'@ },
@{ t='[P1-19] User-impact alert rules (5xx rate, p95)'; l='type:infra,area:ops'; b=@'
**Story:** As the owner, I want to be alerted when users are affected, not on CPU graphs.

**Spec:** section 7

**Acceptance criteria**
- [ ] Alert: 5xx rate > 5% over 5m on key journey routes
- [ ] Alert: p95 latency > 1s over 5m
- [ ] Quiet periods read as Normal (no No-Data noise)
- [ ] Demonstrated firing on injected errors and resolving afterwards
'@ },
@{ t='[P1-20] On-call agent: alert webhook -> diagnose -> issue + fix PR'; l='type:feature,area:ops'; b=@'
**Story:** As the owner, I want an agent that wakes on an alert and fixes the problem.

**Acceptance criteria**
- [ ] Webhook receiver for Grafana alerts (adapted from HW4 responder)
- [ ] Gathers metrics, logs, traces for the alert window and launches a headless coding agent
- [ ] Agent opens a `type:bug` issue and a fix PR referencing it
- [ ] Demo: injected bug -> alert -> fix PR merged -> alert resolves; incident note in `ops/incidents/`
'@ },
@{ t='[P1-21] Agent role prompts in .claude/agents/'; l='type:docs'; b=@'
**Story:** As the human lead, I want each agent role defined so the team works consistently.

**Acceptance criteria**
- [ ] One file per role from docs/agent-team.md (product, planner, backend, frontend, test, reviewer, devops, on-call)
- [ ] Each file states responsibilities, inputs, outputs and allowed tools
- [ ] docs/agent-team.md links to them
'@ },
@{ t='[P1-22] README: setup, run, test, deploy, demo'; l='type:docs'; b=@'
**Story:** As a peer reviewer, I want to understand and run the project from the README alone.

**Acceptance criteria**
- [ ] Problem, features, architecture diagram, tech stack
- [ ] Commands: run locally (one command), test (one command), deploy
- [ ] Dev/prod URLs, screenshots, link to tracker board
- [ ] Short section mapping each rubric criterion to evidence
'@ }
)

# ---------- project board ----------
$projects = gh project list --owner $Owner --format json | ConvertFrom-Json
$proj = $projects.projects | Where-Object { $_.title -eq $ProjectTitle } | Select-Object -First 1
if (-not $proj) {
  $proj = gh project create --owner $Owner --title $ProjectTitle --format json | ConvertFrom-Json
  Write-Host "Created project board #$($proj.number)"
}
gh project edit $proj.number --owner $Owner --visibility PUBLIC | Out-Null
try { gh project link $proj.number --owner $Owner --repo $Repo | Out-Null } catch { Write-Host 'Board already linked to repo (or link not supported) - continuing.' }

# ---------- create issues + add to board ----------
$existing = gh issue list --repo $Repo --label project-1 --state all --limit 200 --json title,url | ConvertFrom-Json
$tmp = New-TemporaryFile
foreach ($i in $issues) {
  $hit = $existing | Where-Object { $_.title -eq $i.t } | Select-Object -First 1
  if ($hit) {
    $url = $hit.url
    Write-Host "skip (exists): $($i.t)"
  } else {
    [System.IO.File]::WriteAllText($tmp.FullName, $i.b)
    $url = gh issue create --repo $Repo --title $i.t --body-file $tmp.FullName --label "project-1,$($i.l)"
    Write-Host "created: $url"
  }
  gh project item-add $proj.number --owner $Owner --url $url | Out-Null
}
Remove-Item $tmp -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "Done. Board: https://github.com/users/$Owner/projects/$($proj.number)"
Write-Host "Issues:  https://github.com/$Repo/issues?q=label%3Aproject-1"
