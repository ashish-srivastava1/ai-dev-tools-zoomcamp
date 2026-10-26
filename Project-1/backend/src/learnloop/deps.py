"""FastAPI dependencies: DB session and write-token guard."""

import hmac
from collections.abc import Iterator

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

_bearer = HTTPBearer(auto_error=False)


def get_db(request: Request) -> Iterator[Session]:
    yield from request.app.state.db.session()


def require_write(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> None:
    """When WRITE_TOKEN is set, mutating calls must send it as a bearer token."""
    token = request.app.state.config.write_token
    if not token:
        return
    supplied = creds.credentials if creds else ""
    if not hmac.compare_digest(supplied.encode(), token.encode()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing or invalid write token",
            headers={"WWW-Authenticate": "Bearer"},
        )
