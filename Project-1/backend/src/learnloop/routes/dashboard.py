import datetime as dt
from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import logic
from ..deps import get_db
from ..models import Module, StudySession, Track
from ..schemas import (
    Dashboard,
    SessionOut,
    Streak,
    TrackProgress,
    WeekHours,
    WeekSummary,
)
from ._common import get_settings

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("", response_model=Dashboard)
def dashboard(db: Session = Depends(get_db)):
    settings = get_settings(db)
    today = logic.today_in(settings.timezone)
    week_start = logic.week_start_of(today, settings.week_start)

    tracks = list(
        db.scalars(select(Track).where(Track.archived.is_(False)).order_by(Track.created_at))
    )
    track_ids = [t.id for t in tracks]

    # Minutes per day for active tracks, up to today (AC4.1, AC4.2, AC4.4).
    minutes_by_day: dict[dt.date, int] = {}
    minutes_by_track: dict[int, int] = defaultdict(int)
    if track_ids:
        rows = db.execute(
            select(StudySession.date, func.sum(StudySession.minutes))
            .where(StudySession.track_id.in_(track_ids), StudySession.date <= today)
            .group_by(StudySession.date)
        ).all()
        minutes_by_day = {d: int(m) for d, m in rows}
        for tid, m in db.execute(
            select(StudySession.track_id, func.sum(StudySession.minutes))
            .where(StudySession.track_id.in_(track_ids))
            .group_by(StudySession.track_id)
        ).all():
            minutes_by_track[tid] = int(m)

    # Module counts per track (AC4.3 / AC2.2).
    module_totals: dict[int, int] = defaultdict(int)
    module_done: dict[int, int] = defaultdict(int)
    if track_ids:
        for tid, status, n in db.execute(
            select(Module.track_id, Module.status, func.count())
            .where(Module.track_id.in_(track_ids))
            .group_by(Module.track_id, Module.status)
        ).all():
            module_totals[tid] += n
            if status == "done":
                module_done[tid] += n

    week_minutes = sum(m for d, m in minutes_by_day.items() if week_start <= d <= today)
    current, longest = logic.streaks(minutes_by_day.keys(), today)

    progress = []
    for t in tracks:
        h = logic.hours(minutes_by_track[t.id])
        progress.append(
            TrackProgress(
                track_id=t.id,
                name=t.name,
                color=t.color,
                hours=h,
                target_hours=t.target_hours,
                target_percent=logic.percent(h, t.target_hours),
                module_count=module_totals[t.id],
                completion_percent=logic.completion_percent(module_done[t.id], module_totals[t.id]),
            )
        )

    recent = []
    if track_ids:
        recent = db.scalars(
            select(StudySession)
            .where(StudySession.track_id.in_(track_ids))
            .order_by(
                StudySession.date.desc(), StudySession.created_at.desc(), StudySession.id.desc()
            )
            .limit(5)
        ).all()

    week_hours = logic.hours(week_minutes)
    return Dashboard(
        empty=not tracks,
        today=today,
        timezone=settings.timezone,
        week=WeekSummary(
            start=week_start,
            hours=week_hours,
            goal_hours=settings.weekly_goal_hours,
            percent=logic.percent(week_hours, settings.weekly_goal_hours),
        ),
        streak=Streak(current_days=current, longest_days=longest),
        tracks=progress,
        weekly_trend=[
            WeekHours(week_start=s, hours=h)
            for s, h in logic.weekly_trend(minutes_by_day, week_start, 8)
        ],
        recent_sessions=[SessionOut.model_validate(s) for s in recent],
    )
