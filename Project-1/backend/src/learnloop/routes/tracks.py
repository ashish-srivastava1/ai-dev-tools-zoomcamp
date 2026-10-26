from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..deps import get_db, require_write
from ..models import Track
from ..schemas import TrackCreate, TrackOut, TrackUpdate
from ._common import get_track, invalid

router = APIRouter(prefix="/api/tracks", tags=["tracks"])


def _ensure_unique(db: Session, name: str, exclude_id: int | None = None) -> None:
    q = select(Track.id).where(Track.name_key == name.lower())
    if exclude_id is not None:
        q = q.where(Track.id != exclude_id)
    if db.scalar(q) is not None:
        raise invalid(f"a track named '{name}' already exists")


@router.get("", response_model=list[TrackOut])
def list_tracks(include_archived: bool = False, db: Session = Depends(get_db)):
    q = select(Track).order_by(Track.created_at, Track.id)
    if not include_archived:
        q = q.where(Track.archived.is_(False))
    return db.scalars(q).all()


@router.post("", response_model=TrackOut, status_code=201, dependencies=[Depends(require_write)])
def create_track(body: TrackCreate, db: Session = Depends(get_db)):
    _ensure_unique(db, body.name)
    track = Track(**body.model_dump(), name_key=body.name.lower(), archived=False)
    db.add(track)
    db.commit()
    db.refresh(track)
    return track


@router.get("/{track_id}", response_model=TrackOut)
def read_track(track_id: int, db: Session = Depends(get_db)):
    return get_track(db, track_id)


@router.patch("/{track_id}", response_model=TrackOut, dependencies=[Depends(require_write)])
def update_track(track_id: int, body: TrackUpdate, db: Session = Depends(get_db)):
    track = get_track(db, track_id)
    changes = body.model_dump(exclude_unset=True)
    if "name" in changes:
        _ensure_unique(db, changes["name"], exclude_id=track_id)
        track.name_key = changes["name"].lower()
    for key, value in changes.items():
        setattr(track, key, value)
    db.commit()
    db.refresh(track)
    return track
