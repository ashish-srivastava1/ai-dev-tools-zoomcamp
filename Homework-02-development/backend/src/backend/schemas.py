from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

Status = Literal["waiting", "called", "seated", "removed"]


class PartyCreate(BaseModel):
    name: str = Field(min_length=1)
    party_size: int = Field(ge=1)
    phone_number: str = Field(min_length=1)
    notes: str = ""

    @field_validator("name", "phone_number")
    @classmethod
    def not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @field_validator("notes")
    @classmethod
    def strip_notes(cls, value: str) -> str:
        return value.strip()


class Party(BaseModel):
    id: str
    code: str
    name: str
    party_size: int
    phone_number: str
    notes: str
    status: Status
    created_at: datetime
    called_at: datetime | None
    seated_at: datetime | None
    removed_at: datetime | None
    position: int | None
    parties_ahead: int | None
    estimated_wait_minutes: int | None


class Stats(BaseModel):
    waiting_count: int
    called_count: int
    avg_wait_today_minutes: int | None


class Error(BaseModel):
    detail: str
