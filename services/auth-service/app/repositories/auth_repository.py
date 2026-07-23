from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.membership import ModuleMembership
from app.models.module import Module
from app.models.permission import Permission
from app.models.refresh_token import RefreshToken
from app.models.role_permission import RolePermission
from app.models.user import User


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(func.lower(User.email) == email.lower()))
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: UUID) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_all_active_modules(session: AsyncSession) -> list[Module]:
    result = await session.execute(select(Module).where(Module.status == "active").order_by(Module.sort_order.asc(), Module.code.asc()))
    return list(result.scalars().all())


async def get_memberships_for_user(session: AsyncSession, user_id: UUID) -> list[ModuleMembership]:
    result = await session.execute(
        select(ModuleMembership)
        .options(joinedload(ModuleMembership.module))
        .join(Module, Module.id == ModuleMembership.module_id)
        .where(ModuleMembership.user_id == user_id, ModuleMembership.status == "active", Module.status == "active")
        .order_by(Module.sort_order.asc(), Module.code.asc())
    )
    return list(result.scalars().all())


async def get_permissions_for_module_role(session: AsyncSession, module_id: UUID, role: str) -> list[Permission]:
    result = await session.execute(
        select(Permission)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .where(RolePermission.module_id == module_id, RolePermission.role == role)
        .order_by(Permission.code.asc())
    )
    return list(result.scalars().all())


async def get_all_permissions_for_module(session: AsyncSession, module_id: UUID) -> list[Permission]:
    result = await session.execute(select(Permission).where(Permission.module_id == module_id).order_by(Permission.code.asc()))
    return list(result.scalars().all())


async def get_refresh_token_by_hash(session: AsyncSession, token_hash: str) -> RefreshToken | None:
    result = await session.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    return result.scalar_one_or_none()


async def create_refresh_token(session: AsyncSession, refresh_token: RefreshToken) -> RefreshToken:
    session.add(refresh_token)
    await session.flush()
    return refresh_token


async def revoke_refresh_token(session: AsyncSession, refresh_token: RefreshToken, replaced_by_token_id: UUID | None = None) -> RefreshToken:
    refresh_token.revoked_at = utc_now()
    refresh_token.replaced_by_token_id = replaced_by_token_id
    await session.flush()
    return refresh_token


async def update_last_login(session: AsyncSession, user: User) -> User:
    user.last_login_at = utc_now()
    await session.flush()
    return user


async def create_audit_log(session: AsyncSession, audit_log: AuditLog) -> AuditLog:
    session.add(audit_log)
    await session.flush()
    return audit_log
