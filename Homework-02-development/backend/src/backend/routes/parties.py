from fastapi import APIRouter, Depends, HTTPException

from ..deps import get_store
from ..schemas import Party, PartyCreate
from ..store import InvalidTransitionError, PartyNotFoundError, PartyStore

router = APIRouter(prefix="/api/parties", tags=["parties"])


@router.get("", response_model=list[Party])
def list_parties(store: PartyStore = Depends(get_store)):
    return store.list_all_out()


@router.post("", response_model=Party, status_code=201)
def add_party(payload: PartyCreate, store: PartyStore = Depends(get_store)):
    party = store.add(**payload.model_dump())
    return store.to_out_dict(party)


@router.post("/{party_id}/call", response_model=Party)
def call_party(party_id: str, store: PartyStore = Depends(get_store)):
    try:
        party = store.call(party_id)
    except PartyNotFoundError:
        raise HTTPException(status_code=404, detail="Party not found.") from None
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    return store.to_out_dict(party)


@router.post("/{party_id}/seat", response_model=Party)
def seat_party(party_id: str, store: PartyStore = Depends(get_store)):
    try:
        party = store.seat(party_id)
    except PartyNotFoundError:
        raise HTTPException(status_code=404, detail="Party not found.") from None
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    return store.to_out_dict(party)


@router.post("/{party_id}/remove", response_model=Party)
def remove_party(party_id: str, store: PartyStore = Depends(get_store)):
    try:
        party = store.remove(party_id)
    except PartyNotFoundError:
        raise HTTPException(status_code=404, detail="Party not found.") from None
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    return store.to_out_dict(party)
