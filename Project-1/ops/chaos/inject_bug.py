"""Chaos: deliberately break the key journey for the on-call demo.

Replaces the guarded body of ``completion_percent`` in backend/src/learnloop/logic.py with an
unguarded division, so ``GET /api/dashboard`` returns 500 whenever an active track has zero
modules (ZeroDivisionError). This is the "bad deploy" the on-call agent has to find and fix.

    python ops/chaos/inject_bug.py            # inject (idempotent)
    python ops/chaos/inject_bug.py --revert   # restore the correct code
    python ops/chaos/inject_bug.py --status   # show current state

Stdlib only. Refuses to touch the file if neither the good nor the bad text is found.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

TARGET = Path(__file__).resolve().parents[2] / "backend" / "src" / "learnloop" / "logic.py"

DOC = '    """Module completion % (AC2.2): 0 when the track has no modules."""\n'
GOOD = DOC + "    return percent(done, total)\n"
BAD = DOC + "    return int(done * 100 / total + 0.5)\n"


def state(text: str) -> str:
    if GOOD in text:
        return "healthy"
    if BAD in text:
        return "injected"
    return "unknown"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--revert", action="store_true", help="restore the correct code")
    group.add_argument("--status", action="store_true", help="print current state only")
    ap.add_argument("--file", type=Path, default=TARGET, help=argparse.SUPPRESS)
    args = ap.parse_args(argv)

    path: Path = args.file
    if not path.exists():
        print(f"error: {path} not found", file=sys.stderr)
        return 2
    text = path.read_text(encoding="utf-8")
    current = state(text)

    if args.status:
        print(f"{path}: {current}")
        return 0
    if current == "unknown":
        print(
            f"error: expected completion_percent body not found in {path}; "
            "refusing to modify (has the code changed or been fixed differently?)",
            file=sys.stderr,
        )
        return 1

    if args.revert:
        if current == "healthy":
            print("already healthy - nothing to revert")
            return 0
        path.write_text(text.replace(BAD, GOOD, 1), encoding="utf-8")
        print(f"reverted: completion_percent guarded again in {path}")
        return 0

    if current == "injected":
        print("bug already injected - nothing to do")
        return 0
    path.write_text(text.replace(GOOD, BAD, 1), encoding="utf-8")
    print(
        f"injected: completion_percent now divides by zero for tracks without modules\n"
        f"  file: {path}\n"
        "  next: rebuild the app (docker compose up --build -d app), then run "
        "python ops/chaos/traffic.py"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
