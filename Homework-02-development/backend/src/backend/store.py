"""In-memory mock of the parties table.

This is a placeholder for a real database (SQLite via SQLAlchemy, added
later in the homework). Routes only depend on the public methods below, so
swapping the backing store later shouldn't require route changes.
"""

from __future__ import annotations

import itertools
import random
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

Status = Literal["waiting", "called", "seated", "removed"]

DEFAULT_AVG_SEATING_MINUTES = 15
_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no 0/O/1/I
_CODE_LENGTH = 4


class PartyNotFoundError(Exception):
    pass


class InvalidTransitionError(Exception):
    pass


@dataclass
class Party:
    id: str
    code: str
    name: str
    party_size: int
    phone_number: str
    notes: str
    status: Status
    created_at: datetime
    seq: int
    called_at: datetime | None = None
    seated_at: datetime | None = None
    removed_at: datetime | None = None


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PartyStore:
    def __init__(self) -> None:
        self._parties: dict[str, Party] = {}
        self._seq = itertools.count()

    # -- mutations ---------------------------------------------------

    def add(self, *, name: str, party_size: int, phone_number: str, notes: str) -> Party:
        party = Party(
            id=str(uuid.uuid4()),
            code=self._generate_code(),
            name=name,
            party_size=party_size,
            phone_number=phone_number,
            notes=notes,
            status="waiting",
            created_at=_utcnow(),
            seq=next(self._seq),
        )
        self._parties[party.id] = party
        return party

    def call(self, party_id: str) -> Party:
        party = self.get(party_id)
        if party.status != "waiting":
            raise InvalidTransitionError("Only waiting parties can be called.")
        party.status = "called"
        party.called_at = _utcnow()
        return party

    def seat(self, party_id: str) -> Party:
        party = self.get(party_id)
        if party.status not in ("waiting", "called"):
            raise InvalidTransitionError("Only waiting or called parties can be seated.")
        party.status = "seated"
        party.seated_at = _utcnow()
        return party

    def remove(self, party_id: str) -> Party:
        party = self.get(party_id)
        if party.status not in ("waiting", "called"):
            raise InvalidTransitionError("Only waiting or called parties can be removed.")
        party.status = "removed"
        party.removed_at = _utcnow()
        return party

    # -- reads ---------------------------------------------------------

    def get(self, party_id: str) -> Party:
        try:
            return self._parties[party_id]
        except KeyError:
            raise PartyNotFoundError(party_id) from None

    def list_all(self) -> list[Party]:
        return sorted(self._parties.values(), key=lambda p: (p.created_at, p.seq))

    def waiting_in_order(self) -> list[Party]:
        return sorted(
            (p for p in self._parties.values() if p.status == "waiting"),
            key=lambda p: (p.created_at, p.seq),
        )

    def find_by_code(self, code: str) -> Party | None:
        normalized = code.strip().upper()
        for party in self._parties.values():
            if party.code == normalized:
                return party
        return None

    def find_by_phone(self, phone_number: str) -> Party | None:
        normalized = phone_number.strip()
        matches = [p for p in self._parties.values() if p.phone_number == normalized]
        if not matches:
            return None
        return max(matches, key=lambda p: (p.created_at, p.seq))

    def average_seating_minutes(self) -> float:
        completed = [p for p in self._parties.values() if p.status == "seated" and p.seated_at]
        if not completed:
            return DEFAULT_AVG_SEATING_MINUTES
        total = sum((p.seated_at - p.created_at).total_seconds() / 60 for p in completed)
        return total / len(completed)

    def stats(self) -> dict:
        waiting_count = sum(1 for p in self._parties.values() if p.status == "waiting")
        called_count = sum(1 for p in self._parties.values() if p.status == "called")

        today = _utcnow().date()
        seated_today = [
            p
            for p in self._parties.values()
            if p.status == "seated" and p.seated_at and p.seated_at.date() == today
        ]
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

    def to_out_dict(self, party: Party) -> dict:
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

    def _generate_code(self) -> str:
        existing = {p.code for p in self._parties.values()}
        while True:
            code = "".join(random.choices(_CODE_ALPHABET, k=_CODE_LENGTH))
            if code not in existing:
                return code
