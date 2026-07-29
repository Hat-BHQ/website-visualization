from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings, get_settings
from app.core.redis import RedisLockManager, create_redis_client
from app.db.session import create_engine
from app.models.marketplace import (
    EtsyListing,
    EtsyListingMatch,
    EtsyListingSnapshot,
    EbayListing,
    EbayListingMatch,
    EbayListingSnapshot,
    ReverbListing,
    ReverbListingMatch,
    ReverbListingSnapshot,
)
from app.models.system import ResearchTarget, SyncError, SyncJob
from app.sync.google_sheets import read_sheet_rows
from app.sync.normalize import normalize_listing_row

UTC = timezone.utc
SHEET_NAMES = {
    "ebay": "Raw data ebay",
    "reverb": "Raw data reverb",
    "etsy": "Raw data etsy",
}
LOCK_KEYS = {
    "ebay": "sync:hqa:ebay",
    "reverb": "sync:hqa:reverb",
    "etsy": "sync:hqa:etsy",
}

MARKETPLACE_MODELS: dict[str, dict[str, Any]] = {
    "ebay": {
        "listing": EbayListing,
        "match": EbayListingMatch,
        "snapshot": EbayListingSnapshot,
        "seller_field": "seller_name",
    },
    "reverb": {
        "listing": ReverbListing,
        "match": ReverbListingMatch,
        "snapshot": ReverbListingSnapshot,
        "seller_field": "shop_name",
    },
    "etsy": {
        "listing": EtsyListing,
        "match": EtsyListingMatch,
        "snapshot": EtsyListingSnapshot,
        "seller_field": "shop_name",
    },
}


@dataclass
class SyncStats:
    total_source_rows: int = 0
    inserted_rows: int = 0
    updated_rows: int = 0
    unchanged_rows: int = 0
    skipped_rows: int = 0
    error_rows: int = 0


async def _get_or_create_job(
    session: AsyncSession,
    marketplace: str,
    trigger_type: str,
    job_id: UUID | None,
) -> SyncJob:
    now = datetime.now(tz=UTC)
    if job_id is None:
        job = SyncJob(
            marketplace=marketplace,
            trigger_type=trigger_type,
            status="running",
            started_at=now,
            total_source_rows=0,
            inserted_rows=0,
            updated_rows=0,
            unchanged_rows=0,
            skipped_rows=0,
            error_rows=0,
        )
        session.add(job)
        await session.flush()
        return job

    existing = await session.get(SyncJob, job_id)
    if existing is None:
        raise LookupError(f"Sync job not found: {job_id}")

    existing.status = "running"
    existing.started_at = now
    existing.completed_at = None
    await session.flush()
    return existing


async def _find_active_job_id(session: AsyncSession, marketplace: str) -> UUID | None:
    stmt = (
        select(SyncJob.id)
        .where(
            SyncJob.marketplace == marketplace,
            SyncJob.status.in_(["queued", "running"]),
        )
        .order_by(SyncJob.created_at.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def _upsert_research_target(
    session: AsyncSession, target_payload: dict[str, Any]
) -> ResearchTarget | None:
    product_code = target_payload.get("product_code")
    if not product_code:
        return None

    result = await session.execute(
        select(ResearchTarget).where(ResearchTarget.product_code == product_code)
    )
    target = result.scalar_one_or_none()
    if target is None:
        target = ResearchTarget(
            product_code=product_code,
            brand=target_payload.get("brand"),
            model=target_payload.get("model"),
            target_category=target_payload.get("target_category"),
            is_active=True,
        )
        session.add(target)
        await session.flush()
        return target

    target.brand = target_payload.get("brand") or target.brand
    target.model = target_payload.get("model") or target.model
    target.target_category = (
        target_payload.get("target_category") or target.target_category
    )
    await session.flush()
    return target


async def _upsert_listing(
    session: AsyncSession, marketplace: str, listing_payload: dict[str, Any]
) -> tuple[Any, str]:
    listing_model = MARKETPLACE_MODELS[marketplace]["listing"]
    result = await session.execute(
        select(listing_model).where(
            listing_model.external_listing_id == listing_payload["external_listing_id"]
        )
    )
    existing = result.scalar_one_or_none()
    now = datetime.now(tz=UTC)

    if existing is None:
        listing = listing_model(**listing_payload)
        listing.first_seen_at = now
        listing.last_seen_at = now
        session.add(listing)
        await session.flush()
        return listing, "inserted"

    changed = existing.state_hash != listing_payload.get("state_hash")
    for key, value in listing_payload.items():
        if key in {"external_listing_id", "first_seen_at", "created_at"}:
            continue
        setattr(existing, key, value)
    existing.last_seen_at = now
    await session.flush()
    return existing, "updated" if changed else "unchanged"


async def _upsert_listing_match(
    session: AsyncSession,
    marketplace: str,
    listing_id: UUID,
    target: ResearchTarget | None,
    match_payload: dict[str, Any],
) -> None:
    if target is None:
        return
    keyword = match_payload.get("keyword")
    if not keyword:
        return

    match_model = MARKETPLACE_MODELS[marketplace]["match"]
    stmt: Select = select(match_model).where(
        match_model.listing_id == listing_id,
        match_model.research_target_id == target.id,
        match_model.keyword == keyword,
        match_model.research_date == match_payload.get("research_date"),
    )
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing is not None:
        return

    match = match_model(
        listing_id=listing_id,
        research_target_id=target.id,
        keyword=keyword,
        match_type=match_payload.get("match_type"),
        exclude_flag=bool(match_payload.get("exclude_flag")),
        raw_confidence=match_payload.get("raw_confidence"),
        research_date=match_payload.get("research_date"),
    )
    session.add(match)
    await session.flush()


async def _create_snapshot_if_changed(
    session: AsyncSession,
    marketplace: str,
    listing: Any,
    action: str,
) -> None:
    if action == "unchanged":
        return

    snapshot_model = MARKETPLACE_MODELS[marketplace]["snapshot"]
    snapshot = snapshot_model(
        listing_id=listing.id,
        observed_at=datetime.now(tz=UTC),
        price=listing.current_price,
        shipping_price=listing.shipping_price,
        total_price=listing.total_price,
        currency=listing.currency,
        quantity=None,
        listing_views=listing.listing_views,
        listing_status=listing.listing_status,
        status_reason=getattr(listing, "status_reason", None),
        state_hash=listing.state_hash or "",
        raw_payload=listing.raw_payload,
    )
    session.add(snapshot)
    await session.flush()


async def _record_row_error(
    session: AsyncSession,
    job: SyncJob,
    marketplace: str,
    row_number: int,
    row: dict[str, str],
    error: Exception,
) -> None:
    session.add(
        SyncError(
            sync_job_id=job.id,
            marketplace=marketplace,
            source_sheet=SHEET_NAMES[marketplace],
            source_row_number=row_number,
            external_listing_id=row.get("external_listing_id")
            or row.get("id")
            or row.get("listing_id"),
            processing_stage="pipeline",
            error_code=error.__class__.__name__,
            error_message=str(error),
            raw_row=row,
        )
    )
    await session.flush()


async def run_marketplace_sync(
    marketplace: str,
    trigger_type: str = "scheduled",
    job_id: UUID | None = None,
    lock_token: str | None = None,
    settings: Settings | None = None,
) -> dict[str, Any]:
    if marketplace not in SHEET_NAMES:
        raise ValueError(f"Unsupported marketplace: {marketplace}")

    settings = settings or get_settings()
    redis_client = create_redis_client(settings.redis_url)
    lock_manager = RedisLockManager(redis_client)
    lock_key = LOCK_KEYS[marketplace]

    owner = lock_token or lock_manager.acquire(lock_key)
    if owner is None:
        engine = create_engine(settings)
        sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
        try:
            async with sessionmaker() as session:
                active_job_id = await _find_active_job_id(session, marketplace)
                return {
                    "status": "conflict",
                    "marketplace": marketplace,
                    "active_job_id": str(active_job_id) if active_job_id else None,
                }
        finally:
            await engine.dispose()

    engine = create_engine(settings)
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    sheet_name = SHEET_NAMES.get(marketplace)
    try:
        async with sessionmaker() as session:
            job = await _get_or_create_job(session, marketplace, trigger_type, job_id)
            rows = read_sheet_rows(
                spreadsheet_id=settings.google_spreadsheet_id,
                oauth_token_file=settings.google_oauth_token_file,
                sheet_name=sheet_name,
            )

            stats = SyncStats(total_source_rows=len(rows))
            for index, row in enumerate(rows, start=2):
                try:
                    async with session.begin_nested():
                        normalized = normalize_listing_row(marketplace, row)
                        target = await _upsert_research_target(
                            session, normalized["target"]
                        )
                        listing, action = await _upsert_listing(
                            session, marketplace, normalized["listing"]
                        )
                        await _upsert_listing_match(
                            session,
                            marketplace,
                            listing.id,
                            target,
                            normalized["match"],
                        )
                        await _create_snapshot_if_changed(
                            session, marketplace, listing, action
                        )

                        if action == "inserted":
                            stats.inserted_rows += 1
                        elif action == "updated":
                            stats.updated_rows += 1
                        else:
                            stats.unchanged_rows += 1
                except Exception as row_error:
                    stats.error_rows += 1
                    await _record_row_error(
                        session, job, marketplace, index, row, row_error
                    )

            job.total_source_rows = stats.total_source_rows
            job.inserted_rows = stats.inserted_rows
            job.updated_rows = stats.updated_rows
            job.unchanged_rows = stats.unchanged_rows
            job.skipped_rows = stats.skipped_rows
            job.error_rows = stats.error_rows
            job.status = "partial_success" if stats.error_rows > 0 else "success"
            job.completed_at = datetime.now(tz=UTC)
            job.error_summary = (
                f"{stats.error_rows} rows failed" if stats.error_rows else None
            )
            await session.commit()

            return {
                "status": job.status,
                "job_id": str(job.id),
                "marketplace": marketplace,
                "stats": {
                    "total_source_rows": stats.total_source_rows,
                    "inserted_rows": stats.inserted_rows,
                    "updated_rows": stats.updated_rows,
                    "unchanged_rows": stats.unchanged_rows,
                    "skipped_rows": stats.skipped_rows,
                    "error_rows": stats.error_rows,
                },
            }
    except Exception:
        async with sessionmaker() as session:
            if job_id is not None:
                job = await session.get(SyncJob, job_id)
                if job is not None:
                    job.status = "failed"
                    job.completed_at = datetime.now(tz=UTC)
                    await session.commit()
        raise
    finally:
        lock_manager.release(lock_key, owner)
        await engine.dispose()
