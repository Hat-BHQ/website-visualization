from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import Module, ModuleMembership, Permission, RolePermission, User


async def get_user_by_id(session: AsyncSession, user_id):
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_modules_for_user(session: AsyncSession, user_id):
    result = await session.execute(
        select(ModuleMembership, Module)
        .join(Module, Module.id == ModuleMembership.module_id)
        .where(ModuleMembership.user_id == user_id, ModuleMembership.status == "active", Module.status == "active")
        .order_by(Module.sort_order.asc(), Module.code.asc())
    )
    return list(result.all())


async def get_all_modules(session: AsyncSession):
    result = await session.execute(select(Module).where(Module.status == "active").order_by(Module.sort_order.asc(), Module.code.asc()))
    return list(result.scalars().all())


async def get_permissions_for_module_role(session: AsyncSession, module_id, role: str):
    result = await session.execute(
        select(Permission)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .where(RolePermission.module_id == module_id, RolePermission.role == role)
        .order_by(Permission.code.asc())
    )
    return list(result.scalars().all())


async def get_all_permissions_for_module(session: AsyncSession, module_id):
    result = await session.execute(select(Permission).where(Permission.module_id == module_id).order_by(Permission.code.asc()))
    return list(result.scalars().all())
