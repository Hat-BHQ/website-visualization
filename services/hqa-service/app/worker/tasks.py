from __future__ import annotations

import asyncio
from uuid import UUID

from app.sync.pipeline import run_marketplace_sync
from app.worker.celery_app import celery_app


@celery_app.task(name="app.worker.tasks.sync_ebay")
def sync_ebay(job_id: str | None = None, lock_token: str | None = None, trigger_type: str = "scheduled"):
    parsed_job_id = UUID(job_id) if job_id else None
    return asyncio.run(run_marketplace_sync("ebay", trigger_type=trigger_type, job_id=parsed_job_id, lock_token=lock_token))


@celery_app.task(name="app.worker.tasks.sync_reverb")
def sync_reverb(job_id: str | None = None, lock_token: str | None = None, trigger_type: str = "scheduled"):
    parsed_job_id = UUID(job_id) if job_id else None
    return asyncio.run(run_marketplace_sync("reverb", trigger_type=trigger_type, job_id=parsed_job_id, lock_token=lock_token))


@celery_app.task(name="app.worker.tasks.sync_etsy")
def sync_etsy(job_id: str | None = None, lock_token: str | None = None, trigger_type: str = "scheduled"):
    parsed_job_id = UUID(job_id) if job_id else None
    return asyncio.run(run_marketplace_sync("etsy", trigger_type=trigger_type, job_id=parsed_job_id, lock_token=lock_token))
