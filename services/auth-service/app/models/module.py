from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base
from app.models.enums import ModuleStatus


class Module(Base):
    __tablename__ = "modules"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    frontend_path: Mapped[str] = mapped_column(String(255), nullable=False)
    api_prefix: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[ModuleStatus] = mapped_column(String(20), nullable=False, default=ModuleStatus.active, server_default="active")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    permissions = relationship("Permission", back_populates="module", cascade="all, delete-orphan")
    memberships = relationship("ModuleMembership", back_populates="module", cascade="all, delete-orphan")
    role_permissions = relationship("RolePermission", back_populates="module", cascade="all, delete-orphan")
