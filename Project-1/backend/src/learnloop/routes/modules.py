from fastapi import APIRouter, Depends, Response
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from ..deps import get_db, require_write
from ..models import Module, StudySession
from ..schemas import ModuleCreate, ModuleOrder, ModuleOut, ModuleUpdate
from ._common import get_module, get_track, invalid

router = APIRouter(tags=["modules"])


def _modules_of(db: Session, track_id: int) -> list[Module]:
    return list(
        db.scalars(
            select(Module).where(Module.track_id == track_id).order_by(Module.position, Module.id)
        )
    )


@router.get("/api/tracks/{track_id}/modules", response_model=list[ModuleOut])
def list_modules(track_id: int, db: Session = Depends(get_db)):
    get_track(db, track_id)
    return _modules_of(db, track_id)


@router.post(
    "/api/tracks/{track_id}/modules",
    response_model=ModuleOut,
    status_code=201,
    dependencies=[Depends(require_write)],
)
def create_module(track_id: int, body: ModuleCreate, db: Session = Depends(get_db)):
    get_track(db, track_id)
    last = db.scalar(select(func.max(Module.position)).where(Module.track_id == track_id))
    module = Module(
        track_id=track_id, position=(last + 1) if last is not None else 0, **body.model_dump()
    )
    db.add(module)
    db.commit()
    db.refresh(module)
    return module


@router.put(
    "/api/tracks/{track_id}/modules/order",
    response_model=list[ModuleOut],
    dependencies=[Depends(require_write)],
)
def reorder_modules(track_id: int, body: ModuleOrder, db: Session = Depends(get_db)):
    get_track(db, track_id)
    modules = _modules_of(db, track_id)
    if len(body.module_ids) != len(set(body.module_ids)) or set(body.module_ids) != {
        m.id for m in modules
    }:
        raise invalid("module_ids must list every module of the track exactly once")
    by_id = {m.id: m for m in modules}
    for pos, mid in enumerate(body.module_ids):
        by_id[mid].position = pos
    db.commit()
    return _modules_of(db, track_id)


@router.patch(
    "/api/modules/{module_id}", response_model=ModuleOut, dependencies=[Depends(require_write)]
)
def update_module(module_id: int, body: ModuleUpdate, db: Session = Depends(get_db)):
    module = get_module(db, module_id)
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(module, key, value)
    db.commit()
    db.refresh(module)
    return module


@router.delete("/api/modules/{module_id}", status_code=204, dependencies=[Depends(require_write)])
def delete_module(module_id: int, db: Session = Depends(get_db)):
    module = get_module(db, module_id)
    # Keep the sessions, just detach them (AC2.3). Done explicitly so it works on SQLite too.
    db.execute(
        update(StudySession).where(StudySession.module_id == module_id).values(module_id=None)
    )
    db.delete(module)
    db.commit()
    return Response(status_code=204)
