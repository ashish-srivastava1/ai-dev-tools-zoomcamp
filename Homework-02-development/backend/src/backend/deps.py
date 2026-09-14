from fastapi import Depends
from sqlalchemy.orm import Session

from .db import get_session
from .store import PartyStore


def get_store(session: Session = Depends(get_session)) -> PartyStore:
    return PartyStore(session)
