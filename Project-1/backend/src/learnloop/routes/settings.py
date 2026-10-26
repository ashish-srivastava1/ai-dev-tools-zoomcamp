from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..deps import get_db, require_write
from ..schemas import SettingsModel
from ._common import get_settings

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=SettingsModel)
def read_settings(db: Session = Depends(get_db)):
    return SettingsModel.model_validate(get_settings(db))


@router.put("", response_model=SettingsModel, dependencies=[Depends(require_write)])
def replace_settings(body: SettingsModel, db: Session = Depends(get_db)):
    row = get_settings(db)
    for key, value in body.model_dump().items():
        setattr(row, key, value)
    db.commit()
    return SettingsModel.model_validate(row)
