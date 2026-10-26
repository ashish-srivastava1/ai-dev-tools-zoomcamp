"""Gather evidence from Prometheus, Loki and Tempo for an alert window."""

from __future__ import annotations

import json
import os
import time

import httpx

PROM_URL = os.getenv("PROM_URL", "http://localhost:9090")
LOKI_URL = os.getenv("LOKI_URL", "http://localhost:3100")
TEMPO_URL = os.getenv("TEMPO_URL", "http://localhost:3200")
SERVICE = os.getenv("ONCALL_SERVICE", "learnloop")
TIMEOUT = float(os.getenv("ONCALL_HTTP_TIMEOUT", "10"))

PROM_QUERIES = {
    "error_5xx_by_route_5m": (
        'sum by (http_route, http_method, http_status_code) '
        '(increase(learnloop_http_requests_total{http_status_code=~"5.."}[5m]))'
    ),
    "error_ratio_by_route_5m": (
        'sum by (http_route) (rate(learnloop_http_requests_total{http_status_code=~"5.."}[5m]))'
        ' / sum by (http_route) (rate(learnloop_http_requests_total[5m]))'
    ),
    "p95_latency_seconds_by_route_5m": (
        "histogram_quantile(0.95, sum by (le, http_route) "
        "(rate(learnloop_http_request_duration_seconds_bucket[5m])))"
    ),
}


def gather_metrics() -> dict:
    out = {}
    for name, query in PROM_QUERIES.items():
        try:
            r = httpx.get(f"{PROM_URL}/api/v1/query", params={"query": query}, timeout=TIMEOUT)
            data = r.json().get("data", {}).get("result", [])
            out[name] = [{"labels": s.get("metric", {}), "value": s.get("value", [None, None])[1]}
                         for s in data]
        except Exception as exc:  # noqa: BLE001 - evidence is best-effort
            out[name] = {"error": str(exc)}
    return out


def gather_error_logs(minutes: int = 30, limit: int = 50) -> dict:
    end = time.time_ns()
    start = end - minutes * 60 * 1_000_000_000
    # App logs arrive in Loki via OTLP; level lives in the severity_text structured metadata.
    query = os.getenv(
        "ONCALL_LOKI_QUERY",
        f'{{service_name="{SERVICE}"}} | severity_text=~"(?i)error|critical|fatal"',
    )
    try:
        r = httpx.get(
            f"{LOKI_URL}/loki/api/v1/query_range",
            params={"query": query, "start": start, "end": end, "limit": limit,
                    "direction": "backward"},
            timeout=TIMEOUT,
        )
        streams = r.json().get("data", {}).get("result", [])
        lines = []
        for s in streams:
            for _ts, line in s.get("values", []):
                lines.append(line)
        return {"query": query, "count": len(lines), "lines": lines[:limit]}
    except Exception as exc:  # noqa: BLE001
        return {"query": query, "error": str(exc)}


def gather_error_traces(minutes: int = 30, full: int = 2) -> dict:
    now = int(time.time())
    q = f'{{ resource.service.name = "{SERVICE}" && status = error }}'
    try:
        r = httpx.get(
            f"{TEMPO_URL}/api/search",
            params={"q": q, "limit": 20, "start": now - minutes * 60, "end": now},
            timeout=TIMEOUT,
        )
        found = r.json().get("traces", []) or []
    except Exception as exc:  # noqa: BLE001
        return {"query": q, "error": str(exc)}
    details = []
    for t in found[:full]:
        tid = t.get("traceID")
        try:
            tr = httpx.get(f"{TEMPO_URL}/api/traces/{tid}", timeout=TIMEOUT)
            details.append({"trace_id": tid, "trace": _summarise_trace(tr.json())})
        except Exception as exc:  # noqa: BLE001
            details.append({"trace_id": tid, "error": str(exc)})
    return {
        "query": q,
        "matches": [{"trace_id": t.get("traceID"), "root": t.get("rootTraceName"),
                     "duration_ms": t.get("durationMs")} for t in found],
        "details": details,
    }


def _summarise_trace(trace_json: dict) -> list[dict]:
    """Flatten an OTLP-JSON trace into span name/status/exception events (compact for prompts)."""
    spans = []
    for batch in trace_json.get("batches", trace_json.get("resourceSpans", [])) or []:
        for scope in batch.get("scopeSpans", batch.get("instrumentationLibrarySpans", [])) or []:
            for sp in scope.get("spans", []) or []:
                events = [
                    {a["key"]: next(iter(a.get("value", {}).values()), None)
                     for a in ev.get("attributes", [])}
                    for ev in sp.get("events", []) or []
                    if ev.get("name") == "exception"
                ]
                spans.append({
                    "name": sp.get("name"),
                    "status": (sp.get("status") or {}).get("code"),
                    "exceptions": events,
                })
    return spans


def gather_all() -> dict:
    return {
        "metric": gather_metrics(),
        "logs": gather_error_logs(),
        "traces": gather_error_traces(),
    }


if __name__ == "__main__":  # quick manual check: python telemetry_sources.py
    print(json.dumps(gather_all(), indent=2)[:4000])
