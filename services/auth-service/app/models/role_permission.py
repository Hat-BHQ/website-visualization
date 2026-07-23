from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base


class RolePermission(Base):
    __tablename__ = "role_permissions"
    __table_args__ = (UniqueConstraint("module_id", "role", "permission_id", name="uq_role_permissions_module_role_permission"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("modules.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    permission_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False, index=True)

    module = relationship("Module", back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")
