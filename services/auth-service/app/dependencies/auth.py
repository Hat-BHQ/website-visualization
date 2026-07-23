from __future__ import annotations

from uuid import UUID

import jwt
from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_session_from_app


async def get_db_session(session: AsyncSession = Depends(get_session_from_app)) -> AsyncSession:
    return session


async def get_current_user_claims(
    request: Request,
    authorization: str | None = Header(default=None),
) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing access token")
    token = authorization.split(" ", 1)[1].strip()
    settings = request.app.state.settings
    try:
        payload = decode_access_token(settings, token)
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token") from exc
    return payload


async def get_current_user_id(claims: dict = Depends(get_current_user_claims)) -> UUID:
    return UUID(claims["sub"])
