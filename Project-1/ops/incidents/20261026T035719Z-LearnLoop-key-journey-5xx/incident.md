# Incident 20261026T035719Z-LearnLoop-key-journey-5xx

- **Alert:** LearnLoop key journey 5xx
- **Status:** agent_done
- **Received:** 2026-10-26T03:57:19.633335+00:00
- **Resolved:** -
- **Endpoint:** POST /api/sessions, GET /api/dashboard
- **Summary:** LearnLoop key journey is failing for users
- **Agent backend:** claude CLI

## Evidence
Saved alongside this file: `alert.json`, `metric.json`, `logs.json`, `traces.json`, `prompt.txt`.

## Agent outcome
Fixed: `completion_percent` no longer raises `ZeroDivisionError` for tracks with no modules, which was causing the `/api/dashboard` 500s. The fix is uncommitted in the working tree and needs a rebuild to confirm the alert clears.

## Agent findings
- **Symptom:** `GET /api/dashboard` returned 500 for ~83% of requests (45 5xx in 5m). `POST /api/sessions` was not failing; latency was normal (p95 ~25 ms). Loki and Tempo were unreachable (connection refused), so the cause was found by code inspection and by reproducing it with tests.
- **Root cause:** `logic.completion_percent(done, total)` in `backend/src/learnloop/logic.py` computed `done * 100 / total` with no zero guard. Any active track with no modules raised `ZeroDivisionError` in the dashboard handler, which gave a 500. This contradicts AC2.2 (completion is 0 when a track has no modules) and the function's own docstring.
- **Fix:** `completion_percent` now delegates to the existing guarded `percent()` helper, which returns 0 when the total is 0. No error is swallowed, validation is unchanged and the API contract is unchanged.
- **Tests:** The regression tests `test_completion_percent_zero_modules_is_zero` and `test_completion_percent_never_divides_by_zero` (`backend/tests/unit/test_logic.py`) already existed. Before the fix they failed, along with 11 dashboard-dependent tests, 13 failures in all, all `ZeroDivisionError`. After the fix `uv run pytest -q` gives 74 passed.
- **Verify:** Rebuild and redeploy the app (`docker compose up -d --build app`), load the dashboard with a track that has no modules, and log a session. Watch the 5xx ratio for `/api/dashboard` drop to 0 and the Grafana alert return to Normal.
- **Notes:** Git was disabled, so no branch, commit, issue or PR was made. The fix is in the working tree for the lead to review. Loki and Tempo being unreachable during the incident is a separate follow-up.
