"""Party store, backed by a real database via SQLAlchemy.

Routes only depend on `PartyStore`'s public methods (see routes/*.py), so
this is the one place that knows about SQL — swapping databases later
should mean changing `db.py`'s `DATABASE_URL`, not this file.
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import PartyRow

DEFAULT_AVG_SEATING_MINUTES = 15
_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no 0/O/1/I
_CODE_LENGTH = 4

# The row *is* the domain object here — routes and tests read/write its
# attributes directly, same as they did with the old in-memory dataclass.
Party = PartyRow


class PartyNotFoundError(Exception):
    pass


class InvalidTransitionError(Exception):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PartyStore:
    def __init__(self, session: Session) -> None:
        self._session = session

    # -- mutations ---------------------------------------------------

    def add(self, *, name: str, party_size: int, phone_number: str, notes: str) -> PartyRow:
        row = PartyRow(
            id=str(uuid.uuid4()),
            code=self._generate_code(),
            name=name,
            party_size=party_size,
            phone_number=phone_number,
            notes=notes,
            status="waiting",
            created_at=_utcnow(),
        )
        self._session.add(row)
        self._session.commit()
        return row

    def call(self, party_id: str) -> PartyRow:
        party = self.get(party_id)
        if party.status != "waiting":
            raise InvalidTransitionError("Only waiting parties can be called.")
        party.status = "called"
        party.called_at = _utcnow()
        self._session.commit()
        return party

    def seat(self, party_id: str) -> PartyRow:
        party = self.get(party_id)
        if party.status not in ("waiting", "called"):
            raise InvalidTransitionError("Only waiting or called parties can be seated.")
        party.status = "seated"
        party.seated_at = _utcnow()
        self._session.commit()
        return party

    def remove(self, party_id: str) -> PartyRow:
        party = self.get(party_id)
        if party.status not in ("waiting", "called"):
            raise InvalidTransitionError("Only waiting or called parties can be removed.")
        party.status = "removed"
        party.removed_at = _utcnow()
        self._session.commit()
        return party

    # -- reads ---------------------------------------------------------

    def get(self, party_id: str) -> PartyRow:
        party = self._session.scalar(select(PartyRow).where(PartyRow.id == party_id))
        if party is None:
            raise PartyNotFoundError(party_id)
        return party

    def list_all(self) -> list[PartyRow]:
        stmt = select(PartyRow).order_by(PartyRow.created_at, PartyRow.seq)
        return list(self._session.scalars(stmt))

    def waiting_in_order(self) -> list[PartyRow]:
        stmt = (
            select(PartyRow)
            .where(PartyRow.status == "waiting")
            .order_by(PartyRow.created_at, PartyRow.seq)
        )
        return list(self._session.scalars(stmt))

    def find_by_code(self, code: str) -> PartyRow | None:
        normalized = code.strip().upper()
        return self._session.scalar(select(PartyRow).where(PartyRow.code == normalized))

    def find_by_phone(self, phone_number: str) -> PartyRow | None:
        normalized = phone_number.strip()
        stmt = (
            select(PartyRow)
            .where(PartyRow.phone_number == normalized)
            .order_by(PartyRow.created_at.desc(), PartyRow.seq.desc())
            .limit(1)
        )
        return self._session.scalar(stmt)

    def average_seating_minutes(self) -> float:
        completed = self._seated_rows()
        if not completed:
            return DEFAULT_AVG_SEATING_MINUTES
        total = sum((p.seated_at - p.created_at).total_seconds() / 60 for p in completed)
        return total / len(completed)

    def stats(self) -> dict:
        waiting_count = self._count_where(PartyRow.status == "waiting")
        called_count = self._count_where(PartyRow.status == "called")

        today = _utcnow().date()
        seated_today = [p for p in self._seated_rows() if p.seated_at.date() == today]

        avg_wait_today_minutes = None
        if seated_today:
            total = sum((p.seated_at - p.created_at).total_seconds() / 60 for p in seated_today)
            avg_wait_today_minutes = round(total / len(seated_today))

        return {
            "waiting_count": waiting_count,
            "called_count": called_count,
            "avg_wait_today_minutes": avg_wait_today_minutes,
        }

    # -- derived view --------------------------------------------------

    def to_out_dict(self, party: PartyRow) -> dict:
        """Party fields plus queue position / wait estimate, computed fresh."""
        base = {
            "id": party.id,
            "code": party.code,
            "name": party.name,
            "party_size": party.party_size,
            "phone_number": party.phone_number,
            "notes": party.notes,
            "status": party.status,
            "created_at": party.created_at,
            "called_at": party.called_at,
            "seated_at": party.seated_at,
            "removed_at": party.removed_at,
        }

        if party.status == "waiting":
            waiting = self.waiting_in_order()
            position = next(i for i, p in enumerate(waiting) if p.id == party.id) + 1
            parties_ahead = position - 1
            estimated_wait_minutes = round(parties_ahead * self.average_seating_minutes())
            base.update(
                position=position,
                parties_ahead=parties_ahead,
                estimated_wait_minutes=estimated_wait_minutes,
            )
        elif party.status == "called":
            base.update(position=None, parties_ahead=0, estimated_wait_minutes=0)
        else:
            base.update(position=None, parties_ahead=None, estimated_wait_minutes=None)

        return base

    def list_all_out(self) -> list[dict]:
        return [self.to_out_dict(p) for p in self.list_all()]

    # -- internals -------------------------------------------------------

    def _seated_rows(self) -> list[PartyRow]:
        stmt = select(PartyRow).where(PartyRow.status == "seated", PartyRow.seated_at.is_not(None))
        return list(self._session.scalars(stmt))

    def _count_where(self, *clauses) -> int:
        stmt = select(func.count()).select_from(PartyRow).where(*clauses)
        return self._session.scalar(stmt) or 0

    def _generate_code(self) -> str:
        existing = set(self._session.scalars(select(PartyRow.code)))
        while True:
            code = "".join(random.choices(_CODE_ALPHABET, k=_CODE_LENGTH))
            if code not in existing:
                return code
