from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid
from sqlalchemy import JSON

from app.db.base import Base

json_variant = JSON().with_variant(JSONB, "postgresql")


class ResearchTarget(Base):
    __tablename__ = "research_targets"
    __table_args__ = {"schema": "hqa_system"}

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_code: Mapped[str] = mapped_column(Text, unique=True, nullable=False, index=True)
    brand: Mapped[str | None] = mapped_column(Text, nullable=True)
    model: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_category: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class SyncJob(Base):
    __tablename__ = "sync_jobs"
    __table_args__ = {"schema": "hqa_system"}

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    marketplace: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    trigger_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_source_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    inserted_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    updated_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    unchanged_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    skipped_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    error_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    requested_by_user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True, index=True)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", json_variant, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class SyncError(Base):
    __tablename__ = "sync_errors"
    __table_args__ = {"schema": "hqa_system"}

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sync_job_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("hqa_system.sync_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    marketplace: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    source_sheet: Mapped[str] = mapped_column(Text, nullable=False)
    source_row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    external_listing_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_stage: Mapped[str] = mapped_column(Text, nullable=False)
    error_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    raw_row: Mapped[dict | None] = mapped_column(json_variant, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
