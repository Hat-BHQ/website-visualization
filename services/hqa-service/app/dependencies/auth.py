from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

import jwt
from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_session_from_app
from app.services.auth_service import CurrentUserContext, load_current_user_context


async def get_db_session(session: AsyncSession = Depends(get_session_from_app)) -> AsyncSession:
    return session


async def get_current_user_context(
    request: Request,
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_db_session),
) -> CurrentUserContext:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing access token")

    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_access_token(request.app.state.settings, token)
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token") from exc

    try:
        _ = session
        return await load_current_user_context(request.app.state.settings.auth_service_url, token, UUID(payload["sub"]))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc


def require_permission(permission: str, module_code: str):
    async def dependency(user: CurrentUserContext = Depends(get_current_user_context)) -> CurrentUserContext:
        if not user.has_permission(module_code, permission):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user

    return dependency


def require_module(module_code: str):
    async def dependency(user: CurrentUserContext = Depends(get_current_user_context)) -> CurrentUserContext:
        if not user.has_module(module_code):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user

    return dependency
