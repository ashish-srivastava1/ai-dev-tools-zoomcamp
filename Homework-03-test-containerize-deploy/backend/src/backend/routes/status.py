from fastapi import APIRouter, Depends, HTTPException, Query

from ..deps import get_store
from ..schemas import Party
from ..store import PartyStore

router = APIRouter(prefix="/api", tags=["status"])


@router.get("/status", response_model=Party)
def get_status(
    code: str | None = Query(default=None),
    phone_number: str | None = Query(default=None),
    store: PartyStore = Depends(get_store),
):
    if not code and not phone_number:
        raise HTTPException(status_code=422, detail="Provide a code or phone_number.")

    party = store.find_by_code(code) if code else store.find_by_phone(phone_number)
    if party is None:
        raise HTTPException(status_code=404, detail="No matching party found.")

    return store.to_out_dict(party)
