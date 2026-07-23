from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserModule(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    role: str
    frontend_path: str
    permissions: list[str]


class CurrentUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str
    is_superadmin: bool
    modules: list[UserModule]
