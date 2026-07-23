from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

import httpx
from fastapi import HTTPException, status

from app.schemas.auth import CurrentUser, UserModule


@dataclass(slots=True)
class CurrentUserContext:
    id: UUID
    email: str
    full_name: str
    is_superadmin: bool
    modules: list[UserModule]

    def has_module(self, module_code: str) -> bool:
        if self.is_superadmin:
            return True
        normalized = module_code.lower()
        return any(module.code.lower() == normalized for module in self.modules)

    def has_permission(self, module_code: str, permission: str) -> bool:
        if self.is_superadmin:
            return True
        normalized = module_code.lower()
        for module in self.modules:
            if module.code.lower() == normalized and permission in module.permissions:
                return True
        return False


async def load_current_user_context(auth_service_url: str, token: str, user_id: UUID) -> CurrentUserContext:
    headers = {"Authorization": f"Bearer {token}"}
    timeout = httpx.Timeout(connect=3.0, read=5.0, write=5.0, pool=5.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(f"{auth_service_url.rstrip('/')}/api/auth/me", headers=headers)

    if response.status_code == status.HTTP_401_UNAUTHORIZED:
        raise LookupError("Invalid token")
    if response.status_code >= 400:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Auth service unavailable")

    payload = CurrentUser.model_validate(response.json())
    if payload.id != user_id:
        raise LookupError("Token subject mismatch")

    return CurrentUserContext(
        id=payload.id,
        email=payload.email,
        full_name=payload.full_name,
        is_superadmin=payload.is_superadmin,
        modules=[UserModule.model_validate(module) for module in payload.modules],
    )
