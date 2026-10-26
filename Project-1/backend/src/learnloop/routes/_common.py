from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models import Module, StudySession, Track, UserSettings


def not_found(what: str) -> HTTPException:
    return HTTPException(status_code=404, detail=f"{what} not found")


def invalid(msg: str) -> HTTPException:
    return HTTPException(status_code=422, detail=msg)


def get_track(db: Session, track_id: int) -> Track:
    track = db.get(Track, track_id)
    if track is None:
        raise not_found("track")
    return track


def get_module(db: Session, module_id: int) -> Module:
    module = db.get(Module, module_id)
    if module is None:
        raise not_found("module")
    return module


def get_session(db: Session, session_id: int) -> StudySession:
    s = db.get(StudySession, session_id)
    if s is None:
        raise not_found("session")
    return s


def get_settings(db: Session) -> UserSettings:
    row = db.get(UserSettings, 1)
    if row is None:
        row = UserSettings(
            id=1, weekly_goal_hours=5.0, timezone="Asia/Kolkata", week_start="monday"
        )
        db.add(row)
        db.commit()
    return row
