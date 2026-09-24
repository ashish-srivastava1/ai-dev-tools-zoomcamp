"""Shared plumbing for the integration tests: locating and driving the
docker-compose stack. Imported by `conftest.py` (for the session fixture) and
by individual test modules (for `compose`/`psql` in persistence checks)."""

from __future__ import annotations

import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

# backend/tests/integration/_stack.py -> repo homework root (4 levels up).
COMPOSE_FILE = Path(__file__).resolve().parents[3] / "docker-compose.yml"
BASE_URL = "http://localhost:8000"


def compose(*args: str, **kwargs) -> subprocess.CompletedProcess:
    """Run a `docker compose` subcommand against this project's compose file."""
    return subprocess.run(
        ["docker", "compose", "-f", str(COMPOSE_FILE), *args],
        check=True,
        **kwargs,
    )


def psql(sql: str) -> str:
    """Run a query directly inside the Postgres container and return the raw
    scalar result (tuples-only, unaligned)."""
    result = compose(
        "exec", "-T", "db",
        "psql", "-U", "tableturn", "-d", "tableturn", "-tAc", sql,
        capture_output=True, text=True,
    )
    return result.stdout.strip()


def wait_for_health(url: str, timeout: float = 150.0) -> None:
    """Poll until the app answers 200, or raise if it never does.

    The app only starts after Postgres is healthy (depends_on: service_healthy),
    and the image builds on first `up`, so the first boot can take a while.
    """
    deadline = time.monotonic() + timeout
    last_err: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                if resp.status == 200:
                    return
        except (urllib.error.URLError, ConnectionError, OSError) as err:
            last_err = err
        time.sleep(1.0)
    raise RuntimeError(f"Stack did not become healthy at {url} within {timeout}s: {last_err}")
