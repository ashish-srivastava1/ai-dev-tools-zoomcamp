"""Chaos: drive traffic through the key journey (log a session -> load the dashboard).

Makes sure an active track WITHOUT modules exists (that's what the injected bug trips on),
then repeatedly calls POST /api/sessions and GET /api/dashboard and prints a status summary.

    python ops/chaos/traffic.py                       # 60 rounds against http://localhost:8000
    python ops/chaos/traffic.py -n 200 --delay 0.2
    python ops/chaos/traffic.py --base-url https://learnloop-dev.onrender.com --token $WRITE_TOKEN

Stdlib only.
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import sys
import time
import urllib.error
import urllib.request

TRACK_NAME = "Chaos demo (no modules)"


def call(base: str, method: str, path: str, body=None, token: str | None = None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(base.rstrip("/") + path, data=data, method=method)
    req.add_header("Accept", "application/json")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    if token and method != "GET":
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        return e.code, None
    except (urllib.error.URLError, TimeoutError) as e:
        return 0, str(e)


def ensure_track(base: str, token: str | None) -> int:
    status, tracks = call(base, "GET", "/api/tracks")
    if status != 200:
        sys.exit(f"cannot list tracks (HTTP {status}): is the app running at {base}?")
    for t in tracks:
        if t["name"] == TRACK_NAME:
            return t["id"]
    status, t = call(base, "POST", "/api/tracks", {"name": TRACK_NAME, "target_hours": 5}, token)
    if status != 201:
        sys.exit(f"cannot create track (HTTP {status}); pass --token if WRITE_TOKEN is set")
    print(f"created track '{TRACK_NAME}' (id {t['id']}) with no modules")
    return t["id"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Drive traffic through the LearnLoop key journey")
    ap.add_argument("--base-url", default="http://localhost:8000")
    ap.add_argument("-n", "--rounds", type=int, default=60)
    ap.add_argument("--delay", type=float, default=0.5, help="seconds between rounds")
    ap.add_argument("--token", default=None, help="WRITE_TOKEN, if the app has one")
    args = ap.parse_args(argv)

    track_id = ensure_track(args.base_url, args.token)
    counts: collections.Counter = collections.Counter()
    for i in range(args.rounds):
        today = dt.date.today().isoformat()  # local date; server rejects only future dates
        s, _ = call(args.base_url, "POST", "/api/sessions",
                    {"track_id": track_id, "date": today, "minutes": 5,
                     "topic": "chaos traffic"}, args.token)
        counts[f"POST /api/sessions {s}"] += 1
        d, _ = call(args.base_url, "GET", "/api/dashboard")
        counts[f"GET /api/dashboard {d}"] += 1
        if (i + 1) % 10 == 0:
            print(f"round {i + 1}/{args.rounds}: " + ", ".join(
                f"{k} x{v}" for k, v in sorted(counts.items())))
        time.sleep(args.delay)
    errors = sum(v for k, v in counts.items() if k.endswith((" 500", " 502", " 503", " 0")))
    print(f"done: {dict(counts)}; server errors: {errors}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
