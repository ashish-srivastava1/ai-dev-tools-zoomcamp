"""SQLAlchemy ORM models.

Deliberately avoids backend-specific types (native timezone-aware
datetimes, native ENUM, JSON columns) so the schema behaves the same on
SQLite as it would on Postgres/MySQL — see the `UTCDateTime` note below and
AGENTS.md's "keep the app database-agnostic" convention.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Integer, String, Text, TypeDecorator
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class UTCDateTime(TypeDecorator):
    """Always stores naive-UTC, always returns timezone-aware UTC.

    SQLite has no native timezone-aware datetime type, so plain
    `DateTime(timezone=True)` silently drops tzinfo on round-trip there.
    Normalizing explicitly, instead of relying on a database-specific
    datetime type, keeps behavior identical across backends.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Any) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("Expected a timezone-aware datetime.")
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    def process_result_value(self, value: datetime | None, dialect: Any) -> datetime | None:
        if value is None:
            return None
        return value.replace(tzinfo=timezone.utc)


class Base(DeclarativeBase):
    pass


class PartyRow(Base):
    __tablename__ = "parties"

    # Internal-only ordering/tiebreak key. `id` (below) is the public
    # identifier — kept separate so it can stay a UUID string without
    # relying on any database's UUID-as-primary-key support.
    seq: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    id: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=False)
    code: Mapped[str] = mapped_column(String(8), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    party_size: Mapped[int] = mapped_column(Integer, nullable=False)
    phone_number: Mapped[str] = mapped_column(String(50), nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    called_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    seated_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    removed_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
