"""Engine/session setup.

Three ways to point this at a database, checked in order:

1. `TURSO_DATABASE_URL` + `TURSO_AUTH_TOKEN` — a remote Turso (libSQL) DB.
   Used in production (see backend/README.md's deploy section); requires
   the `turso` extra (`uv sync --extra turso`), which only installs on
   Linux/macOS — Turso's Python driver has no Windows wheel.
2. `DATABASE_URL` — any other SQLAlchemy URL (e.g. Postgres), for when
   that becomes the setup instead.
3. Falls back to a local SQLite file next to the project, for local dev.

Nothing else in this module (or in `store.py`) assumes SQLite — the store
only uses portable SQLAlchemy Core/ORM, no dialect-specific SQL.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Base

TURSO_DATABASE_URL = os.environ.get("TURSO_DATABASE_URL")
TURSO_AUTH_TOKEN = os.environ.get("TURSO_AUTH_TOKEN")

if TURSO_DATABASE_URL and TURSO_AUTH_TOKEN:
    # e.g. TURSO_DATABASE_URL="libsql://tableturn-me.turso.io" becomes
    # "sqlite+libsql://tableturn-me.turso.io?secure=true"
    DATABASE_URL = f"sqlite+{TURSO_DATABASE_URL}?secure=true"
    _connect_args = {"auth_token": TURSO_AUTH_TOKEN}
else:
    DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "tableturn.db"
    DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")
    # SQLite file connections are single-threaded by default; FastAPI may
    # hand requests to different threads, so relax that for this one case.
    _connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite:///") else {}

engine = create_engine(DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
