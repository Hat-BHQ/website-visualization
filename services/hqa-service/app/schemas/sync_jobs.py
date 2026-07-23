from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SyncJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    marketplace: str
    trigger_type: str
    status: str
    scheduled_for: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    total_source_rows: int
    inserted_rows: int
    updated_rows: int
    unchanged_rows: int
    skipped_rows: int
    error_rows: int
    requested_by_user_id: UUID | None = None
    error_summary: str | None = None
    metadata_: dict | None = None
    created_at: datetime


class SyncErrorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sync_job_id: UUID
    marketplace: str
    source_sheet: str
    source_row_number: int
    external_listing_id: str | None = None
    processing_stage: str
    error_code: str | None = None
    error_message: str
    raw_row: dict | None = None
    created_at: datetime
