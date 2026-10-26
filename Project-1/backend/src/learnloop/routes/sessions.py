import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..deps import get_db, require_write
from ..logic import today_in
from ..models import Module, StudySession
from ..schemas import SessionCreate, SessionOut, SessionPage, SessionUpdate
from ..telemetry import logger
from ._common import get_session, get_settings, get_track, invalid

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def _validate(db: Session, track_id: int, module_id: int | None, day: dt.date) -> None:
    """Business rules from AC3.2 (field limits are enforced by the schema)."""
    try:
        track = get_track(db, track_id)
    except HTTPException as exc:  # 404 -> 422: bad reference inside the body
        raise invalid("track does not exist") from exc
    if track.archived:
        raise invalid("cannot log a session on an archived track")
    if module_id is not None:
        module = db.get(Module, module_id)
        if module is None or module.track_id != track_id:
            raise invalid("module does not belong to the track")
    tz = get_settings(db).timezone
    if day > today_in(tz):
        raise invalid("date cannot be in the future")


@router.get("", response_model=SessionPage)
def list_sessions(
    track_id: int | None = Query(None, ge=1),
    date_from: dt.date | None = Query(None, alias="from"),
    date_to: dt.date | None = Query(None, alias="to"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    filters = []
    if track_id is not None:
        filters.append(StudySession.track_id == track_id)
    if date_from is not None:
        filters.append(StudySession.date >= date_from)
    if date_to is not None:
        filters.append(StudySession.date <= date_to)
    total = db.scalar(select(func.count()).select_from(StudySession).where(*filters)) or 0
    items = db.scalars(
        select(StudySession)
        .where(*filters)
        .order_by(StudySession.date.desc(), StudySession.created_at.desc(), StudySession.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return SessionPage(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=SessionOut, status_code=201, dependencies=[Depends(require_write)])
def create_session(body: SessionCreate, request: Request, db: Session = Depends(get_db)):
    _validate(db, body.track_id, body.module_id, body.date)
    s = StudySession(**body.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    request.app.state.telemetry.session_logged()
    # Ids and numbers only - never the topic or notes (spec section 6).
    logger.info(
        "session logged",
        extra={"session_id": s.id, "track_id": s.track_id, "minutes": s.minutes},
    )
    return s


@router.get("/{session_id}", response_model=SessionOut)
def read_session(session_id: int, db: Session = Depends(get_db)):
    return get_session(db, session_id)


@router.patch("/{session_id}", response_model=SessionOut, dependencies=[Depends(require_write)])
def update_session(session_id: int, body: SessionUpdate, db: Session = Depends(get_db)):
    s = get_session(db, session_id)
    changes = body.model_dump(exclude_unset=True)
    track_id = changes.get("track_id", s.track_id)
    module_id = changes.get("module_id", s.module_id)
    # Moving to another track without naming a module drops the old module.
    if "track_id" in changes and "module_id" not in changes and track_id != s.track_id:
        module_id = None
        changes["module_id"] = None
    _validate(db, track_id, module_id, changes.get("date", s.date))
    for key, value in changes.items():
        setattr(s, key, value)
    db.commit()
    db.refresh(s)
    return s


@router.delete("/{session_id}", status_code=204, dependencies=[Depends(require_write)])
def delete_session(session_id: int, db: Session = Depends(get_db)):
    db.delete(get_session(db, session_id))
    db.commit()
    return Response(status_code=204)
