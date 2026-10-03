"""Launch a coding assistant in headless mode to investigate an incident.

The assistant is pluggable so the responder works whether or not a CLI is
installed yet (the "build now, wire later" path):

1. ``AGENT_CMD`` env var - an explicit command. The incident prompt is passed
   on stdin. Example::

       AGENT_CMD="claude -p --permission-mode acceptEdits"

2. ``claude`` on PATH - invoked as
   ``claude -p <prompt> --permission-mode acceptEdits`` in the repo directory.

3. A built-in stub - no CLI available, so we return a deterministic triage
   message. This keeps the service testable and makes the "wire the real agent
   later" step a one-line env change.
"""

import os
import shutil
import subprocess


def _run_cmd(cmd, prompt, workdir, timeout):
    """Run a command, feeding the prompt on stdin, return combined output."""
    proc = subprocess.run(
        cmd,
        input=prompt,
        cwd=workdir,
        capture_output=True,
        text=True,
        timeout=timeout,
        shell=isinstance(cmd, str),
    )
    out = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    if proc.returncode != 0:
        return f"{out}\n[agent exited {proc.returncode}]\n{err}".strip()
    return out or err


def _stub(prompt, incident):
    """Deterministic fallback when no coding assistant is configured."""
    is_test = incident.get("is_test")
    endpoint = incident.get("endpoint") or "unknown endpoint"
    if is_test:
        return (
            "Incident responder received a TEST notification.\n"
            f"Alert: {incident.get('alertname')}\n"
            "No telemetry anomaly to investigate and no code to change.\n"
            "Verified the responder pipeline end to end: alert parsed, "
            "incident recorded, agent invoked.\n"
            "No action required: this was a test notification with no incident to fix."
        )
    return (
        "Incident responder received a FIRING alert and gathered context.\n"
        f"Affected endpoint: {endpoint}\n"
        f"Summary: {incident.get('summary')}\n"
        "Saved logs, traces and the 5xx metric alongside this incident.\n"
        "No coding assistant is wired up yet (set AGENT_CMD or install the "
        "claude CLI), so I cannot apply a fix automatically.\n"
        "Escalating to a developer: configure the coding assistant to let the "
        "responder investigate and patch the root cause."
    )


def run_agent(prompt, incident, workdir, timeout=900):
    """Invoke the coding assistant and return its textual answer."""
    agent_cmd = os.getenv("AGENT_CMD")
    try:
        if agent_cmd:
            return _run_cmd(agent_cmd, prompt, workdir, timeout)

        claude = shutil.which("claude")
        if claude:
            cmd = [
                claude,
                "-p",
                prompt,
                "--permission-mode",
                os.getenv("CLAUDE_PERMISSION_MODE", "acceptEdits"),
            ]
            return _run_cmd(cmd, prompt, workdir, timeout)

        return _stub(prompt, incident)
    except subprocess.TimeoutExpired:
        return f"[agent timed out after {timeout}s]"
    except Exception as exc:  # noqa: BLE001 - surface any launch failure
        return f"[agent launch failed: {exc}]"


def agent_mode():
    """Report which agent backend is active, for logging/visibility."""
    if os.getenv("AGENT_CMD"):
        return f"AGENT_CMD ({os.getenv('AGENT_CMD')})"
    if shutil.which("claude"):
        return "claude CLI"
    return "stub (no coding assistant configured)"
