from fastapi import APIRouter, Depends

from ..deps import get_store
from ..schemas import Stats
from ..store import PartyStore

router = APIRouter(prefix="/api", tags=["stats"])


@router.get("/stats", response_model=Stats)
def get_stats(store: PartyStore = Depends(get_store)):
    return store.stats()
