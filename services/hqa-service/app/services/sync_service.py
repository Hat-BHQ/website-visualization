from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.redis import RedisLockManager, create_redis_client
from app.models.system import SyncJob
from app.schemas.sync_trigger import BatchSyncTriggerResponse, SyncTriggerResponse
from app.services.auth_service import CurrentUserContext
from app.sync.pipeline import LOCK_KEYS
from app.worker.tasks import sync_ebay, sync_etsy, sync_reverb

SYNC_TASKS = {
    "ebay": sync_ebay,
    "reverb": sync_reverb,
    "etsy": sync_etsy,
}
SYNC_PERMISSIONS = {
    "ebay": "hqa.ebay.sync",
    "reverb": "hqa.reverb.sync",
    "etsy": "hqa.etsy.sync",
}


def _can_sync_marketplace(user: CurrentUserContext, marketplace: str) -> bool:
    if user.is_superadmin:
        return True
    return user.has_permission("hqa", SYNC_PERMISSIONS[marketplace])


async def _find_active_job(session: AsyncSession, marketplace: str) -> SyncJob | None:
    result = await session.execute(
        select(SyncJob)
        .where(SyncJob.marketplace == marketplace, SyncJob.status.in_(["queued", "running"]))
        .order_by(SyncJob.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def enqueue_marketplace_sync(
    session: AsyncSession,
    user: CurrentUserContext,
    marketplace: str,
    trigger_type: str = "manual",
) -> SyncTriggerResponse:
    if marketplace not in SYNC_TASKS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid marketplace")

    if not _can_sync_marketplace(user, marketplace):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    settings = get_settings()
    lock_key = LOCK_KEYS[marketplace]
    lock_manager = RedisLockManager(create_redis_client(settings.redis_url))

    lock_token = lock_manager.acquire(lock_key)
    if lock_token is None:
        active_job = await _find_active_job(session, marketplace)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": f"{marketplace} sync is already running",
                "active_job_id": str(active_job.id) if active_job else None,
                "marketplace": marketplace,
            },
        )

    job = SyncJob(
        marketplace=marketplace,
        trigger_type=trigger_type,
        status="queued",
        requested_by_user_id=user.id,
        metadata_={"lock_key": lock_key, "lock_token": lock_token},
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)

    try:
        SYNC_TASKS[marketplace].delay(job_id=str(job.id), lock_token=lock_token, trigger_type=trigger_type)
    except Exception as queue_error:
        lock_manager.release(lock_key, lock_token)
        job.status = "failed"
        job.error_summary = str(queue_error)
        await session.commit()
        raise

    return SyncTriggerResponse(job_id=job.id, status="queued", marketplace=marketplace)


async def enqueue_all_marketplaces_sync(
    session: AsyncSession,
    user: CurrentUserContext,
    trigger_type: str = "manual",
) -> BatchSyncTriggerResponse:
    allowed = [marketplace for marketplace in ("ebay", "reverb", "etsy") if _can_sync_marketplace(user, marketplace)]
    if not allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    items: list[SyncTriggerResponse] = []
    for marketplace in allowed:
        items.append(await enqueue_marketplace_sync(session, user, marketplace, trigger_type=trigger_type))
    return BatchSyncTriggerResponse(items=items)
