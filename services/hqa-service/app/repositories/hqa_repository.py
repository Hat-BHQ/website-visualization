from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import and_, asc, desc, distinct, func, literal_column, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import HQA_SCHEMAS
from app.core.security import utc_now
from app.models.auth import Module, ModuleMembership, Permission, RolePermission, User
from app.models.marketplace import (
    EtsyListing,
    EtsyListingMatch,
    EtsyListingSnapshot,
    EtsySearchRun,
    EbayListing,
    EbayListingMatch,
    EbayListingSnapshot,
    EbaySearchRun,
    ReverbListing,
    ReverbListingMatch,
    ReverbListingSnapshot,
    ReverbSearchRun,
)
from app.models.system import ResearchTarget, SyncError, SyncJob

MARKETPLACE_MODELS = {
    "ebay": {
        "listing": EbayListing,
        "match": EbayListingMatch,
        "snapshot": EbayListingSnapshot,
        "search": EbaySearchRun,
        "permission": "hqa.ebay.view",
        "seller_field": "seller_name",
        "status_field": "listing_status",
    },
    "reverb": {
        "listing": ReverbListing,
        "match": ReverbListingMatch,
        "snapshot": ReverbListingSnapshot,
        "search": ReverbSearchRun,
        "permission": "hqa.reverb.view",
        "seller_field": "shop_name",
        "status_field": "listing_status",
    },
    "etsy": {
        "listing": EtsyListing,
        "match": EtsyListingMatch,
        "snapshot": EtsyListingSnapshot,
        "search": EtsySearchRun,
        "permission": "hqa.etsy.view",
        "seller_field": "shop_name",
        "status_field": "listing_status",
    },
}


def get_marketplace_config(marketplace: str) -> dict[str, Any]:
    return MARKETPLACE_MODELS[marketplace]


async def get_dashboard_row(session: AsyncSession, listing_model, marketplace: str) -> dict[str, Any]:
    today_start = datetime.combine(utc_now().date(), time.min).replace(tzinfo=timezone.utc)
    tomorrow_start = today_start + timedelta(days=1)
    result = await session.execute(select(func.count(listing_model.id)))
    total_active = int(result.scalar_one() or 0)

    new_today_result = await session.execute(
        select(func.count(listing_model.id)).where(listing_model.first_seen_at >= today_start, listing_model.first_seen_at < tomorrow_start)
    )
    new_today = int(new_today_result.scalar_one() or 0)

    sync_job = await session.execute(
        select(SyncJob)
        .where(SyncJob.marketplace == marketplace)
        .order_by(SyncJob.created_at.desc())
        .limit(1)
    )
    latest_job = sync_job.scalar_one_or_none()
    return {
        "active_listings": total_active,
        "new_today": new_today,
        "last_sync_at": latest_job.completed_at if latest_job else None,
        "sync_status": latest_job.status if latest_job else None,
    }


async def get_dashboard(session: AsyncSession) -> dict[str, dict[str, Any]]:
    ebay = await get_dashboard_row(session, EbayListing, "ebay")
    reverb = await get_dashboard_row(session, ReverbListing, "reverb")
    etsy = await get_dashboard_row(session, EtsyListing, "etsy")
    return {"ebay": ebay, "reverb": reverb, "etsy": etsy}


def apply_date_bounds(statement, column, date_from: date | None, date_to: date | None):
    if date_from:
        statement = statement.where(column >= datetime.combine(date_from, time.min).replace(tzinfo=timezone.utc))
    if date_to:
        statement = statement.where(column < datetime.combine(date_to, time.max).replace(tzinfo=timezone.utc))
    return statement


async def list_listings(
    session: AsyncSession,
    marketplace: str,
    page: int,
    page_size: int,
    q: str | None = None,
    status: str | None = None,
    category: str | None = None,
    condition: str | None = None,
    seller: str | None = None,
    product_id: str | None = None,
    keyword: str | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    sort_by: str | None = None,
    sort_order: str = "desc",
):
    config = get_marketplace_config(marketplace)
    listing_model = config["listing"]
    match_model = config["match"]
    query = select(listing_model)

    if q:
        query = query.where(listing_model.listing_title.ilike(f"%{q}%"))
    if status:
        query = query.where(listing_model.listing_status == status)
    if category:
        query = query.where(or_(listing_model.category_name == category, listing_model.category_id == category))
    if condition:
        query = query.where(or_(listing_model.condition_name == condition, listing_model.condition_id == condition))
    if seller:
        seller_field = getattr(listing_model, config["seller_field"])
        query = query.where(seller_field.ilike(f"%{seller}%"))
    if product_id:
        query = query.join(match_model, match_model.listing_id == listing_model.id).join(
            ResearchTarget, ResearchTarget.id == match_model.research_target_id
        ).where(ResearchTarget.product_code == product_id)
    if keyword:
        query = query.join(match_model, match_model.listing_id == listing_model.id).where(match_model.keyword.ilike(f"%{keyword}%"))
    if min_price is not None:
        query = query.where(listing_model.current_price >= min_price)
    if max_price is not None:
        query = query.where(listing_model.current_price <= max_price)
    query = apply_date_bounds(query, listing_model.published_at, date_from, date_to)
    query = query.distinct()

    total_result = await session.execute(select(func.count()).select_from(query.subquery()))
    total = int(total_result.scalar_one() or 0)

    sort_column = getattr(listing_model, sort_by or "last_seen_at", listing_model.last_seen_at)
    if sort_order.lower() == "asc":
        query = query.order_by(asc(sort_column), asc(listing_model.id))
    else:
        query = query.order_by(desc(sort_column), desc(listing_model.id))

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(query)
    items = list(result.scalars().all())
    return items, total


async def get_listing(session: AsyncSession, marketplace: str, listing_id: UUID):
    listing_model = get_marketplace_config(marketplace)["listing"]
    result = await session.execute(select(listing_model).where(listing_model.id == listing_id))
    return result.scalar_one_or_none()


async def get_listing_history(session: AsyncSession, marketplace: str, listing_id: UUID):
    snapshot_model = get_marketplace_config(marketplace)["snapshot"]
    result = await session.execute(
        select(snapshot_model).where(snapshot_model.listing_id == listing_id).order_by(snapshot_model.observed_at.desc(), snapshot_model.created_at.desc())
    )
    return list(result.scalars().all())


async def list_sync_jobs(session: AsyncSession, marketplace: str | None = None):
    query = select(SyncJob)
    if marketplace:
        query = query.where(SyncJob.marketplace == marketplace)
    result = await session.execute(query.order_by(SyncJob.created_at.desc()))
    return list(result.scalars().all())


async def get_sync_job(session: AsyncSession, job_id: UUID):
    result = await session.execute(select(SyncJob).where(SyncJob.id == job_id))
    return result.scalar_one_or_none()


async def list_sync_errors(session: AsyncSession, job_id: UUID):
    result = await session.execute(select(SyncError).where(SyncError.sync_job_id == job_id).order_by(SyncError.created_at.asc()))
    return list(result.scalars().all())
