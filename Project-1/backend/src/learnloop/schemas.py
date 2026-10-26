"""Pydantic request/response models - mirror components/schemas in openapi.yaml."""

import datetime as dt
from typing import Annotated, ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

HexColor = Annotated[str, Field(pattern=r"^#[0-9a-fA-F]{6}$")]
ModuleStatus = Literal["not_started", "in_progress", "done"]
TrackName = Annotated[str, Field(min_length=1, max_length=80)]
Description = Annotated[str | None, Field(max_length=500)]
TargetHours = Annotated[float, Field(gt=0)]
ModuleTitle = Annotated[str, Field(min_length=1, max_length=120)]
Minutes = Annotated[int, Field(ge=1, le=600)]
Topic = Annotated[str, Field(min_length=1, max_length=120)]
Notes = Annotated[str | None, Field(max_length=2000)]


def _strip(v):
    return v.strip() if isinstance(v, str) else v


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _NonEmptyPatch(_Strict):
    """PATCH bodies must set at least one field (minProperties: 1) and may not null
    out required columns."""

    not_null: ClassVar[tuple[str, ...]] = ()

    @model_validator(mode="after")
    def _check(self):
        if not self.model_fields_set:
            raise ValueError("at least one field must be provided")
        for name in self.not_null:
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null")
        return self


# ---------- tracks ----------
class TrackCreate(_Strict):
    name: TrackName
    description: Description = None
    target_hours: TargetHours
    color: HexColor = "#4f46e5"

    _s = field_validator("name", mode="before")(_strip)


class TrackUpdate(_NonEmptyPatch):
    not_null: ClassVar[tuple[str, ...]] = ("name", "target_hours", "color", "archived")
    name: TrackName | None = None
    description: Description = None
    target_hours: TargetHours | None = None
    color: HexColor | None = None
    archived: bool | None = None

    _s = field_validator("name", mode="before")(_strip)


class TrackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    target_hours: float
    color: str
    archived: bool
    created_at: dt.datetime


# ---------- modules ----------
class ModuleCreate(_Strict):
    title: ModuleTitle
    status: ModuleStatus = "not_started"

    _s = field_validator("title", mode="before")(_strip)


class ModuleUpdate(_NonEmptyPatch):
    not_null: ClassVar[tuple[str, ...]] = ("title", "status")
    title: ModuleTitle | None = None
    status: ModuleStatus | None = None

    _s = field_validator("title", mode="before")(_strip)


class ModuleOrder(_Strict):
    module_ids: list[int]


class ModuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    track_id: int
    title: str
    position: int
    status: ModuleStatus


# ---------- sessions ----------
class SessionCreate(_Strict):
    track_id: int
    module_id: int | None = None
    date: dt.date
    minutes: Minutes
    topic: Topic
    notes: Notes = None

    _s = field_validator("topic", mode="before")(_strip)


class SessionUpdate(_NonEmptyPatch):
    not_null: ClassVar[tuple[str, ...]] = ("track_id", "date", "minutes", "topic")
    track_id: int | None = None
    module_id: int | None = None
    date: dt.date | None = None
    minutes: Minutes | None = None
    topic: Topic | None = None
    notes: Notes = None

    _s = field_validator("topic", mode="before")(_strip)


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    track_id: int
    module_id: int | None
    date: dt.date
    minutes: int
    topic: str
    notes: str | None
    created_at: dt.datetime


class SessionPage(BaseModel):
    items: list[SessionOut]
    total: int
    page: int
    page_size: int


# ---------- settings ----------
class SettingsModel(_Strict):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    weekly_goal_hours: Annotated[float, Field(gt=0, le=168)] = 5
    timezone: str = "Asia/Kolkata"
    week_start: Literal["monday", "sunday"] = "monday"

    @field_validator("timezone")
    @classmethod
    def _valid_tz(cls, v: str) -> str:
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

        try:
            ZoneInfo(v)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError(f"unknown IANA timezone: {v}") from exc
        return v


# ---------- dashboard ----------
class WeekSummary(BaseModel):
    start: dt.date
    hours: float
    goal_hours: float
    percent: int


class Streak(BaseModel):
    current_days: int
    longest_days: int


class TrackProgress(BaseModel):
    track_id: int
    name: str
    color: str
    hours: float
    target_hours: float
    target_percent: int
    module_count: int
    completion_percent: int


class WeekHours(BaseModel):
    week_start: dt.date
    hours: float


class Dashboard(BaseModel):
    empty: bool
    today: dt.date
    timezone: str
    week: WeekSummary
    streak: Streak
    tracks: list[TrackProgress]
    weekly_trend: list[WeekHours]
    recent_sessions: list[SessionOut]
