"""Runtime configuration, read from environment variables only."""

import os
from dataclasses import dataclass
from functools import lru_cache


def normalise_db_url(url: str) -> str:
    """Make hosted Postgres URLs (postgres://, postgresql://) use the psycopg 3 driver."""
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix) :]
    return url


@dataclass(frozen=True)
class Config:
    database_url: str
    write_token: str | None
    app_env: str
    static_dir: str | None
    version: str


@lru_cache
def get_config() -> Config:
    return Config(
        database_url=normalise_db_url(os.getenv("DATABASE_URL", "sqlite:///./learnloop.db")),
        write_token=os.getenv("WRITE_TOKEN") or None,
        app_env=os.getenv("APP_ENV", "local"),
        static_dir=os.getenv("STATIC_DIR") or None,
        version=os.getenv("APP_VERSION", "dev"),
    )
