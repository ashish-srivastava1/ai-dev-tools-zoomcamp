# Incident 20261026T035519Z — LearnLoop key journey 5xx

## Agent findings

**Symptom.** Alert "LearnLoop key journey 5xx" (critical). Metrics show only
`GET /api/dashboard` returning 500 (~75% of its requests in 5m); p95 latency is normal (~24 ms)
and `/api/sessions` shows no 5xx series, so this is a single code path, not a DB or app outage.
Loki and Tempo were unreachable (connection refused), so there was no stack trace. The diagnosis
comes from the runbook's "500 on /api/dashboard only" pattern plus code reading.

**Root cause.** `completion_percent(done, total)` in `backend/src/learnloop/logic.py` computed
`done * 100 / total` with no guard. Its docstring says it returns 0 when the track has no
modules (AC2.2), but it raised `ZeroDivisionError` when `total == 0`. The dashboard route calls
it for every active track, so one track without modules makes the whole dashboard return 500.
That also breaks the second step of the key journey.

**Fix.** Added `if total <= 0: return 0`, the same guard `percent()` already uses. Validation and
the API contract are unchanged, and no exception is swallowed.

**Tests.** Added `test_completion_percent_never_divides_by_zero` in
`backend/tests/unit/test_logic.py`. Existing `test_completion_percent_zero_modules_is_zero`
and `test_completion_zero_when_no_modules` (test_modules.py) also cover this path.
**Not run:** `uv run pytest -q` was blocked by the headless permission prompt, so neither the
failing-first run nor the final green run was done. The lead must run `cd backend && uv run pytest -q`.

**Verify.**
1. Run `make test` or `cd backend && uv run pytest -q`.
2. Rebuild and redeploy the app (`docker compose up -d --build app`).
3. Hit `GET /api/dashboard` and log a session a few times.
4. Watch the 5xx ratio on the LearnLoop dashboard (http://localhost:3001/d/learnloop) fall below
   5% and the alert return to Normal.

Git was disabled (`ONCALL_GIT` is not 1), so the changes are uncommitted in the working tree.
If the rebuild doesn't clear the alert, roll back per `ops/rollback.md`.
