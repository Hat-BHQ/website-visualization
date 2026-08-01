from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
    verify_password,
)
from app.models.audit_log import AuditLog
from app.models.enums import MembershipStatus
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.auth_repository import (
    create_audit_log,
    create_refresh_token,
    get_all_active_modules,
    get_all_permissions_for_module,
    get_memberships_for_user,
    get_permissions_for_module_role,
    get_refresh_token_by_hash,
    get_user_by_email,
    get_user_by_id,
    revoke_refresh_token,
    update_last_login,
)
from app.schemas.auth import MeResponse, ModuleAccess, TokenPair


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class CurrentUser:
    id: UUID
    email: str
    full_name: str
    is_superadmin: bool


async def login(
    session: AsyncSession,
    settings: Settings,
    email: str,
    password: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> TokenPair:
    user = await get_user_by_email(session, email)
    if user is None or user.status != "active" or not verify_password(password, user.password_hash):
        await create_audit_log(
            session,
            AuditLog(
                user_id=user.id if user else None,
                action="auth.login.failed",
                ip_address=ip_address,
                user_agent=user_agent,
                new_data={"email": email},
            ),
        )
        await session.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    await update_last_login(session, user)
    access_token = create_access_token(settings, str(user.id), user.is_superadmin)
    plain_refresh_token = generate_refresh_token()
    refresh_token = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(plain_refresh_token),
        expires_at=utc_now() + timedelta(days=settings.refresh_token_expire_days),
        ip_address=ip_address,
        user_agent=user_agent,
    )
    await create_refresh_token(session, refresh_token)
    await create_audit_log(
        session,
        AuditLog(
            user_id=user.id,
            action="auth.login.success",
            ip_address=ip_address,
            user_agent=user_agent,
            new_data={"user_id": str(user.id)},
        ),
    )
    await session.commit()
    return TokenPair(
        access_token=access_token,
        refresh_token=plain_refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


async def refresh(
    session: AsyncSession,
    settings: Settings,
    refresh_token_value: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> TokenPair:
    token_hash = hash_refresh_token(refresh_token_value)
    current_token = await get_refresh_token_by_hash(session, token_hash)
    if current_token is None or current_token.revoked_at is not None or current_token.expires_at <= utc_now():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = await get_user_by_id(session, current_token.user_id)
    if user is None or user.status != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    new_plain_refresh_token = generate_refresh_token()
    new_refresh_token = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(new_plain_refresh_token),
        expires_at=utc_now() + timedelta(days=settings.refresh_token_expire_days),
        ip_address=ip_address,
        user_agent=user_agent,
    )
    await create_refresh_token(session, new_refresh_token)
    await revoke_refresh_token(session, current_token, replaced_by_token_id=new_refresh_token.id)

    await create_audit_log(
        session,
        AuditLog(
            user_id=user.id,
            action="auth.refresh.success",
            ip_address=ip_address,
            user_agent=user_agent,
            new_data={"old_refresh_token_id": str(current_token.id), "new_refresh_token_id": str(new_refresh_token.id)},
        ),
    )
    await session.commit()
    return TokenPair(
        access_token=create_access_token(settings, str(user.id), user.is_superadmin),
        refresh_token=new_plain_refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


async def logout(session: AsyncSession, refresh_token_value: str, ip_address: str | None = None, user_agent: str | None = None) -> None:
    token_hash = hash_refresh_token(refresh_token_value)
    current_token = await get_refresh_token_by_hash(session, token_hash)
    if current_token is None or current_token.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    await revoke_refresh_token(session, current_token)
    await create_audit_log(
        session,
        AuditLog(
            user_id=current_token.user_id,
            action="auth.logout.success",
            ip_address=ip_address,
            user_agent=user_agent,
            new_data={"refresh_token_id": str(current_token.id)},
        ),
    )
    await session.commit()


async def get_me(session: AsyncSession, user_id: UUID) -> MeResponse:
    user = await get_user_by_id(session, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    modules: list[ModuleAccess] = []
    if user.is_superadmin:
        active_modules = await get_all_active_modules(session)
        for module in active_modules:
            permissions = await get_all_permissions_for_module(session, module.id)
            modules.append(
                ModuleAccess(
                    code=module.code,
                    name=module.name,
                    role="superadmin",
                    frontend_path=module.frontend_path,
                    permissions=[permission.code for permission in permissions],
                )
            )
    else:
        memberships = await get_memberships_for_user(session, user.id)
        for membership in memberships:
            if membership.status != MembershipStatus.active:
                continue
            module = membership.module
            permissions = await get_permissions_for_module_role(session, module.id, membership.role)
            modules.append(
                ModuleAccess(
                    code=module.code,
                    name=module.name,
                    role=membership.role,
                    frontend_path=module.frontend_path,
                    permissions=[permission.code for permission in permissions],
                )
            )

    return MeResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_superadmin=user.is_superadmin,
        modules=modules,
    )
