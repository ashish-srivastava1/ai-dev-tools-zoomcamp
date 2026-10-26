# Incident evidence

Each folder is one alert handled by the on-call agent (`ops/oncall/`):
`alert.json` (webhook payload), `metric.json` / `logs.json` / `traces.json` (telemetry
gathered for the alert window), `prompt.txt` (what the agent was told),
`agent-response.txt` (its answer) and `incident.md` (summary + agent findings).

## Recorded runs (26 Oct 2026, development verification)

Both runs used the real app (exporting OTLP), an OpenTelemetry Collector 0.119.0 and
Prometheus 3.1.0, the injected bug from `ops/chaos/inject_bug.py`, real traffic from
`ops/chaos/traffic.py`, and Claude Code running headless as the agent. Grafana, Loki and
Tempo were not running in that sandbox, so the alert webhook was sent with `curl`
in Grafana's payload format (the 5xx alert query evaluated to 0.38, well above its
0.05 threshold), and the agent's Loki/Tempo lookups show "connection refused".

| Incident | What happened |
|---|---|
| `20261026T035519Z-LearnLoop-key-journey-5xx` | The agent found the `ZeroDivisionError` in `completion_percent` and patched it, but the headless session wasn't allowed to run `pytest`. That led to the `allowed_tools()` guardrail in `ops/oncall/agent_runner.py`, which lets tests and lint run unattended and allows git/gh only with `ONCALL_GIT=1`. |
| `20261026T035719Z-LearnLoop-key-journey-5xx` | Full loop. The alert woke the agent; it found the root cause from metrics plus code, fixed `completion_percent`, ran the suite (74 passed) and wrote `incident.md`. After restarting the app, `traffic.py` showed `GET /api/dashboard 200 x20` and the 5xx rate went back to 0. |

Run the full demo with Grafana on your own machine as described in `ops/runbook.md`.
New incidents land here automatically.
