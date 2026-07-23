from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base
from app.models.enums import MembershipRole, MembershipStatus


class ModuleMembership(Base):
    __tablename__ = "module_memberships"
    __table_args__ = (UniqueConstraint("user_id", "module_id", name="uq_module_memberships_user_module"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    module_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("modules.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[MembershipRole] = mapped_column(String(20), nullable=False)
    status: Mapped[MembershipStatus] = mapped_column(String(20), nullable=False, default=MembershipStatus.active, server_default="active")
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="memberships", foreign_keys=[user_id])
    module = relationship("Module", back_populates="memberships")
    creator = relationship("User", foreign_keys=[created_by])
