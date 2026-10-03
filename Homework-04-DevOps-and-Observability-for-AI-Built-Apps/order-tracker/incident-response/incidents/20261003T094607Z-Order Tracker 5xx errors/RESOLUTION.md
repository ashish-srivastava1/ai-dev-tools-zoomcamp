# Incident resolution

**Alert:** Order Tracker 5xx errors (firing)
**Affected endpoint:** `GET /api/orders/{order_id}`
**Trigger:** `GET /api/orders/express-1002` returned HTTP 500 (x6 in the 5xx metric).

## Root cause

`order_detail()` in `app/main.py` computed the express delivery estimate with:

```python
estimated_at = placed_at.replace(day=placed_at.day + 2)
```

`datetime.replace(day=...)` sets an absolute day-of-month, so for an order
placed near the end of a month it asks for a day that does not exist. The seed
order `express-1002` is created with the last day of the previous month
(2026-09-30), so `day=30 + 2 = 32` raised `ValueError: day is out of range for
month`, which surfaced as an unhandled 500.

## Fix

Use `timedelta` so the two days roll over month and year boundaries:

```python
estimated_at = placed_at + timedelta(days=2)
```

## Verification

- `GET /api/orders/express-1002` now returns 200 with
  `"estimated_delivery": "2026-10-02"` (2026-09-30 + 2 days).
- `uv run --frozen pytest -q` -> 3 passed.
- The Grafana 5xx alert returns to Normal once the 5-minute window clears.

## How this incident was handled

The Grafana alert fired on the 5xx metric and sent a webhook to the incident
responder (`POST /alerts`), which recorded this folder (alert, metric, logs,
traces, prompt) and launched the coding assistant in headless mode. The agent
backend was the stub, which escalated to a developer; the fix above was then
applied. Wiring a real `claude` CLI (set `AGENT_CMD`) lets the responder apply
this class of fix automatically.
