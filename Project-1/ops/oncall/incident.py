"""Pure helpers for the on-call responder: parse Grafana webhooks, dedupe,
build the agent prompt and the incident report. No I/O here, so it is easy to test."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field

SERVICE = "learnloop"


@dataclass
class Alert:
    status: str  # firing | resolved
    alertname: str
    labels: dict
    annotations: dict
    fingerprint: str
    starts_at: str | None = None
    ends_at: str | None = None
    is_test: bool = False
    raw: dict = field(default_factory=dict, repr=False)

    @property
    def key(self) -> str:
        """Identity used for dedupe / resolve matching."""
        return f"{self.alertname}:{self.fingerprint}"

    @property
    def endpoint(self) -> str | None:
        return self.annotations.get("endpoint")

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("raw", None)
        return d


def _fingerprint(labels: dict) -> str:
    blob = json.dumps({k: v for k, v in sorted(labels.items())}, sort_keys=True)
    return hashlib.sha1(blob.encode()).hexdigest()[:16]


def parse_alerts(payload: dict) -> list[Alert]:
    """Turn a Grafana (unified alerting) webhook payload into Alert objects."""
    alerts = []
    for a in payload.get("alerts", []) or []:
        labels = dict(a.get("labels") or {})
        annotations = dict(a.get("annotations") or {})
        alertname = labels.get("alertname") or payload.get("title") or "alert"
        summary = (annotations.get("summary") or "").lower()
        is_test = (
            labels.get("test") == "true"
            or alertname.lower() in {"testalert", "test"}
            or "no incident" in summary
            or "test notification" in summary
        )
        alerts.append(
            Alert(
                status=(a.get("status") or payload.get("status") or "firing").lower(),
                alertname=alertname,
                labels=labels,
                annotations=annotations,
                fingerprint=a.get("fingerprint") or _fingerprint(labels),
                starts_at=a.get("startsAt"),
                ends_at=a.get("endsAt"),
                is_test=is_test,
                raw=a,
            )
        )
    return alerts


def slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-")[:60] or "alert"


def incident_id(alert: Alert, now: dt.datetime | None = None) -> str:
    now = now or dt.datetime.now(dt.UTC)
    return f"{now.strftime('%Y%m%dT%H%M%SZ')}-{slug(alert.alertname)}"


def is_duplicate(
    last_seen: dict[str, dt.datetime], alert: Alert, now: dt.datetime, window_minutes: float
) -> bool:
    """True if the same alert already started an incident within the dedupe window."""
    seen = last_seen.get(alert.key)
    return seen is not None and (now - seen) < dt.timedelta(minutes=window_minutes)


def _clip(obj, limit: int) -> str:
    text = obj if isinstance(obj, str) else json.dumps(obj, indent=2, default=str)
    return text if len(text) <= limit else text[:limit] + "\n... [truncated]"


def build_prompt(
    alert: Alert, context: dict, repo_dir: str, inc_id: str, git_enabled: bool
) -> str:
    """Instructions for the headless coding agent."""
    if alert.is_test:
        return (
            "You are the LearnLoop on-call agent running in headless mode.\n"
            "You received a TEST alert from Grafana. There is no real incident and no code "
            "to change.\n"
            f"Alert: {json.dumps(alert.labels)}\n"
            f"Summary: {alert.annotations.get('summary')}\n\n"
            "Acknowledge the test, confirm the responder pipeline works, and take no action. "
            "End with a single clear last line stating no action was required."
        )

    a = alert.annotations
    git_steps = (
        f"""
6. Git is enabled (ONCALL_GIT=1). From the repository root:
   - `git checkout -b fix/oncall-{inc_id}`
   - commit only the fix and its test, message: "fix(on-call): <what> [incident {inc_id}]"
   - `git push -u origin fix/oncall-{inc_id}`
   - if `gh` is available: create an issue
     `gh issue create --title "[on-call] <short title>" --label "type:bug,area:ops,project-1" `
     `--body "<symptom, root cause, evidence, incident {inc_id}>"`
     then `gh pr create --title "fix(on-call): <short title>" --body "Closes #<issue>\\n\\n<summary>"`
   - put the issue and PR URLs in the incident report."""
        if git_enabled
        else """
6. Git is DISABLED (ONCALL_GIT is not 1): do NOT create branches, commits, issues or PRs.
   Leave the fix in the working tree for the human lead to review."""
    )
    return f"""You are the LearnLoop on-call agent running in headless mode.
Repository (Project-1 of the course repo): {repo_dir}

A Grafana alert just FIRED - real users are affected.
- Alert: {alert.alertname} (severity: {alert.labels.get('severity', 'n/a')})
- Affected endpoint: {a.get('endpoint', 'unknown')}
- Window: {a.get('window', 'unknown')}
- Summary: {a.get('summary', '')}
- Description: {a.get('description', '')}
- Dashboard: {a.get('dashboard_url', 'n/a')}
- Runbook: {a.get('runbook_url', 'ops/runbook.md')}
- Started at: {alert.starts_at}

Evidence gathered from telemetry (also saved under ops/incidents/{inc_id}/):
METRICS (5xx by route, p95 latency):
{_clip(context.get('metric', {}), 2500)}

ERROR LOGS (Loki, newest first):
{_clip(context.get('logs', {}), 4000)}

ERROR TRACES (Tempo):
{_clip(context.get('traces', {}), 3000)}

Do this, in order:
1. Read AGENTS.md and ops/runbook.md. Follow their rules (no PII in logs, uv only, tests first).
2. Find the root cause in backend/src/learnloop/ using the stack trace / error logs above.
3. Reproduce it first: add a failing unit test under backend/tests/unit/ that captures the bug.
4. Fix the root cause with the smallest correct change (do not just catch-and-hide the error,
   do not weaken validation, do not change the API contract).
5. Run `uv run pytest -q` in backend/ and make sure everything passes.{git_steps}
7. Write ops/incidents/{inc_id}/incident.md "## Agent findings" section: symptom, root cause,
   fix, test added, how to verify (rebuild the app and watch the alert resolve).

End your answer with a single clear last line stating the outcome (e.g. "Fixed: ...").
"""


def render_report(incident: dict, context: dict | None = None) -> str:
    """Human-readable incident summary (ops/incidents/<id>/incident.md)."""
    a = incident.get("annotations", {})
    lines = [
        f"# Incident {incident['id']}",
        "",
        f"- **Alert:** {incident.get('alertname')}"
        + (" (TEST)" if incident.get("is_test") else ""),
        f"- **Status:** {incident.get('status')}",
        f"- **Received:** {incident.get('received_at')}",
        f"- **Resolved:** {incident.get('resolved_at') or '-'}",
        f"- **Endpoint:** {a.get('endpoint', '-')}",
        f"- **Summary:** {a.get('summary', '-')}",
        f"- **Agent backend:** {incident.get('agent_backend', '-')}",
        "",
        "## Evidence",
        "Saved alongside this file: `alert.json`, `metric.json`, `logs.json`, `traces.json`, "
        "`prompt.txt`.",
    ]
    if context:
        errs = context.get("logs", {}).get("lines") if isinstance(context.get("logs"), dict) else None
        if errs:
            lines += ["", "Most recent error log lines:", "```"]
            lines += [str(e)[:300] for e in errs[:5]]
            lines += ["```"]
    if incident.get("agent_last_line"):
        lines += ["", "## Agent outcome", incident["agent_last_line"]]
    lines += ["", "## Agent findings", "_The agent appends its findings here._", ""]
    return "\n".join(lines)
