from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user_id, get_db_session
from app.schemas.auth import LoginRequest, LogoutRequest, MeResponse, RefreshRequest, TokenPair
from app.services.auth_service import get_me, login, logout, refresh

router = APIRouter()


@router.post("/login", response_model=TokenPair)
async def login_route(
    payload: LoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> TokenPair:
    settings = request.app.state.settings
    return await login(
        session=session,
        settings=settings,
        email=payload.email,
        password=payload.password,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


@router.post("/refresh", response_model=TokenPair)
async def refresh_route(
    payload: RefreshRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> TokenPair:
    settings = request.app.state.settings
    return await refresh(
        session=session,
        settings=settings,
        refresh_token_value=payload.refresh_token,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


@router.post("/logout")
async def logout_route(
    payload: LogoutRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    await logout(
        session=session,
        refresh_token_value=payload.refresh_token,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return {"status": "ok"}


@router.get("/me", response_model=MeResponse)
async def me_route(
    user_id=Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> MeResponse:
    return await get_me(session, user_id)
