from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class SyncTriggerResponse(BaseModel):
    job_id: UUID
    status: str = "queued"
    marketplace: str


class BatchSyncTriggerResponse(BaseModel):
    items: list[SyncTriggerResponse]
