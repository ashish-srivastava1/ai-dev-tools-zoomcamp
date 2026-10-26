"""Launch a coding assistant in headless mode to investigate and fix an incident.

Backend selection (first match wins):

1. ``AGENT_CMD`` - explicit shell command; the prompt is passed on stdin, e.g.
   ``AGENT_CMD="claude -p --permission-mode acceptEdits"``.
2. ``claude`` on PATH - run as ``claude -p <prompt> --permission-mode <mode>`` in REPO_DIR
   (mode from ``CLAUDE_PERMISSION_MODE``, default ``acceptEdits``).
3. Built-in stub - deterministic triage text so the pipeline is testable without a CLI.
"""

from __future__ import annotations

import os
import shutil
import subprocess


def _run_cmd(cmd, prompt: str, workdir: str, timeout: int) -> str:
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


def _stub(incident: dict) -> str:
    if incident.get("is_test"):
        return (
            "LearnLoop on-call responder received a TEST notification.\n"
            f"Alert: {incident.get('alertname')}\n"
            "Pipeline verified: alert parsed, incident recorded, evidence step skipped, "
            "agent invoked.\n"
            "No action required: this was a test notification with no incident to fix."
        )
    return (
        "LearnLoop on-call responder received a FIRING alert and gathered evidence.\n"
        f"Affected endpoint: {incident.get('annotations', {}).get('endpoint', 'unknown')}\n"
        "Metrics, error logs and error traces are saved in the incident folder.\n"
        "No coding assistant is configured (set AGENT_CMD or install the claude CLI), so no "
        "fix was applied.\n"
        "Escalated to the human lead: see ops/runbook.md to fix manually."
    )


def allowed_tools() -> list[str]:
    """Shell commands the headless agent may run without a human approving each one.

    Guardrail: tests + lint always; git/gh only when ONCALL_GIT=1. Override with
    CLAUDE_ALLOWED_TOOLS (space separated)."""
    override = os.getenv("CLAUDE_ALLOWED_TOOLS")
    if override:
        return override.split()
    tools = ["Read", "Edit", "Write", "Grep", "Glob",
             "Bash(uv run pytest:*)", "Bash(uv run ruff:*)", "Bash(uv sync:*)"]
    if os.getenv("ONCALL_GIT") == "1":
        tools += ["Bash(git:*)", "Bash(gh:*)"]
    return tools


def run_agent(prompt: str, incident: dict, workdir: str, timeout: int | None = None) -> str:
    timeout = timeout or int(os.getenv("AGENT_TIMEOUT", "1200"))
    try:
        agent_cmd = os.getenv("AGENT_CMD")
        if agent_cmd:
            return _run_cmd(agent_cmd, prompt, workdir, timeout)
        claude = shutil.which("claude")
        if claude:
            cmd = [claude, "-p", prompt, "--permission-mode",
                   os.getenv("CLAUDE_PERMISSION_MODE", "acceptEdits"),
                   "--allowedTools", *allowed_tools()]
            return _run_cmd(cmd, prompt, workdir, timeout)
        return _stub(incident)
    except subprocess.TimeoutExpired:
        return f"[agent timed out after {timeout}s]"
    except Exception as exc:  # noqa: BLE001 - surface any launch failure
        return f"[agent launch failed: {exc}]"


def agent_mode() -> str:
    if os.getenv("AGENT_CMD"):
        return f"AGENT_CMD ({os.getenv('AGENT_CMD')})"
    if shutil.which("claude"):
        return "claude CLI"
    return "stub (no coding assistant configured)"
