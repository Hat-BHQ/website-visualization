from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import Iterable

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import create_engine, create_sessionmaker
from app.models.enums import MembershipRole, MembershipStatus, ModuleStatus, UserStatus
from app.models.membership import ModuleMembership
from app.models.module import Module
from app.models.permission import Permission
from app.models.role_permission import RolePermission
from app.models.user import User


@dataclass(slots=True)
class SeedUser:
    email: str
    full_name: str
    is_superadmin: bool = False
    module_roles: list[tuple[str, MembershipRole]] | None = None


MODULES = [
    {
        "code": "HQA",
        "name": "HQ Audio Marketplace",
        "description": "Marketplace operations for HQA",
        "frontend_path": "/hqa",
        "api_prefix": "/api/hqa",
        "sort_order": 1,
    },
    {
        "code": "HQS",
        "name": "HQ Services",
        "description": "Services operations for HQS",
        "frontend_path": "/hqs",
        "api_prefix": "/api/hqs",
        "sort_order": 2,
    },
]

HQA_PERMISSIONS = [
    ("hqa.dashboard.view", "View HQA dashboard"),
    ("hqa.ebay.view", "View eBay listings"),
    ("hqa.ebay.export", "Export eBay listings"),
    ("hqa.ebay.sync", "Sync eBay listings"),
    ("hqa.reverb.view", "View Reverb listings"),
    ("hqa.reverb.export", "Export Reverb listings"),
    ("hqa.reverb.sync", "Sync Reverb listings"),
    ("hqa.etsy.view", "View Etsy listings"),
    ("hqa.etsy.export", "Export Etsy listings"),
    ("hqa.etsy.sync", "Sync Etsy listings"),
    ("hqa.sync_history.view", "View sync history"),
    ("hqa.users.view", "View HQA users"),
    ("hqa.users.manage", "Manage HQA users"),
]

HQS_PERMISSIONS = [
    ("hqs.dashboard.view", "View HQS dashboard"),
    ("hqs.users.view", "View HQS users"),
    ("hqs.users.manage", "Manage HQS users"),
]

SEED_USERS = [
    SeedUser(email="root@company.com", full_name="Superadmin", is_superadmin=True),
    SeedUser(email="admin.hqa@company.com", full_name="HQA Admin", module_roles=[("HQA", MembershipRole.admin)]),
    SeedUser(
        email="user.hqa@company.com",
        full_name="HQA User",
        module_roles=[("HQA", MembershipRole.user)],
    ),
    SeedUser(email="admin.hqs@company.com", full_name="HQS Admin", module_roles=[("HQS", MembershipRole.admin)]),
    SeedUser(
        email="user.hqs@company.com",
        full_name="HQS User",
        module_roles=[("HQS", MembershipRole.user)],
    ),
    SeedUser(
        email="multi@company.com",
        full_name="Multi Module User",
        module_roles=[("HQA", MembershipRole.admin), ("HQS", MembershipRole.user)],
    ),
]


async def upsert_module(session: AsyncSession, *, code: str, values: dict) -> Module:
    result = await session.execute(select(Module).where(Module.code == code))
    module = result.scalar_one_or_none()
    module_values = {key: value for key, value in values.items() if key != "code"}
    if module is None:
        module = Module(code=code, **module_values)
        session.add(module)
        await session.flush()
        return module
    for key, value in module_values.items():
        setattr(module, key, value)
    await session.flush()
    return module


async def upsert_permission(session: AsyncSession, *, module_id, code: str, name: str) -> Permission:
    result = await session.execute(select(Permission).where(Permission.module_id == module_id, Permission.code == code))
    permission = result.scalar_one_or_none()
    if permission is None:
        permission = Permission(module_id=module_id, code=code, name=name)
        session.add(permission)
        await session.flush()
        return permission
    permission.name = name
    await session.flush()
    return permission


async def upsert_user(session: AsyncSession, *, user_data: SeedUser, password_hash: str) -> User:
    result = await session.execute(select(User).where(User.email == user_data.email))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(
            email=user_data.email,
            password_hash=password_hash,
            full_name=user_data.full_name,
            is_superadmin=user_data.is_superadmin,
            status=UserStatus.active,
        )
        session.add(user)
        await session.flush()
        return user
    user.full_name = user_data.full_name
    user.is_superadmin = user_data.is_superadmin
    user.password_hash = password_hash
    user.status = UserStatus.active
    await session.flush()
    return user


async def upsert_membership(session: AsyncSession, *, user_id, module_id, role: MembershipRole, created_by=None) -> ModuleMembership:
    result = await session.execute(select(ModuleMembership).where(ModuleMembership.user_id == user_id, ModuleMembership.module_id == module_id))
    membership = result.scalar_one_or_none()
    if membership is None:
        membership = ModuleMembership(
            user_id=user_id,
            module_id=module_id,
            role=role,
            status=MembershipStatus.active,
            created_by=created_by,
        )
        session.add(membership)
        await session.flush()
        return membership
    membership.role = role
    membership.status = MembershipStatus.active
    membership.created_by = created_by
    await session.flush()
    return membership


async def upsert_role_permission(session: AsyncSession, *, module_id, role: MembershipRole, permission_id) -> RolePermission:
    result = await session.execute(
        select(RolePermission).where(
            RolePermission.module_id == module_id,
            RolePermission.role == role,
            RolePermission.permission_id == permission_id,
        )
    )
    role_permission = result.scalar_one_or_none()
    if role_permission is None:
        role_permission = RolePermission(module_id=module_id, role=role, permission_id=permission_id)
        session.add(role_permission)
        await session.flush()
    return role_permission


async def seed(settings=None) -> None:
    settings = settings or get_settings()
    if not settings.seed_default_password:
        raise RuntimeError("SEED_DEFAULT_PASSWORD must be set before running the seed script")

    engine = create_engine(settings)
    sessionmaker = create_sessionmaker(engine)
    password_hash = hash_password(settings.seed_default_password)

    async with sessionmaker() as session:
        modules_by_code: dict[str, Module] = {}
        for module_data in MODULES:
            module = await upsert_module(session, code=module_data["code"], values=module_data)
            modules_by_code[module.code] = module

        permissions_by_code: dict[str, Permission] = {}
        for code, name in HQA_PERMISSIONS:
            permission = await upsert_permission(session, module_id=modules_by_code["HQA"].id, code=code, name=name)
            permissions_by_code[permission.code] = permission
        for code, name in HQS_PERMISSIONS:
            permission = await upsert_permission(session, module_id=modules_by_code["HQS"].id, code=code, name=name)
            permissions_by_code[permission.code] = permission

        role_permission_map = {
            ("HQA", MembershipRole.admin): [code for code, _ in HQA_PERMISSIONS],
            ("HQA", MembershipRole.user): [
                "hqa.dashboard.view",
                "hqa.ebay.view",
                "hqa.reverb.view",
                "hqa.etsy.view",
                "hqa.sync_history.view",
            ],
            ("HQS", MembershipRole.admin): [code for code, _ in HQS_PERMISSIONS],
            ("HQS", MembershipRole.user): ["hqs.dashboard.view"],
        }

        for (module_code, role), permission_codes in role_permission_map.items():
            for permission_code in permission_codes:
                await upsert_role_permission(
                    session,
                    module_id=modules_by_code[module_code].id,
                    role=role,
                    permission_id=permissions_by_code[permission_code].id,
                )

        users_by_email: dict[str, User] = {}
        for user_data in SEED_USERS:
            user = await upsert_user(session, user_data=user_data, password_hash=password_hash)
            users_by_email[user.email] = user

        root_user = users_by_email["root@company.com"]
        for user_data in SEED_USERS:
            if not user_data.module_roles:
                continue
            user = users_by_email[user_data.email]
            for module_code, role in user_data.module_roles:
                await upsert_membership(
                    session,
                    user_id=user.id,
                    module_id=modules_by_code[module_code].id,
                    role=role,
                    created_by=root_user.id,
                )

        await session.commit()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
