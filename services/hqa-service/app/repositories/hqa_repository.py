from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import (
    and_,
    asc,
    desc,
    distinct,
    func,
    literal_column,
    or_,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import HQA_SCHEMAS
from app.core.security import utc_now
from app.models.auth import (
    Module,
    ModuleMembership,
    Permission,
    RolePermission,
    User,
)
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
from app.models.system import (
    ResearchTarget,
    SyncError,
    SyncJob,
)

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


def get_seller_column(listing_model, config):
    return getattr(listing_model, config["seller_field"])


def get_listing_sort_column(
    listing_model,
    config,
    sort_by: str,
):
    seller_column = get_seller_column(
        listing_model,
        config,
    )

    sort_columns = {
        "last_seen_at": listing_model.last_seen_at,
        "published_at": listing_model.published_at,
        "status": listing_model.listing_status,
        "category": listing_model.category_name,
        "condition": listing_model.condition_name,
        "seller": seller_column,
        "price": listing_model.current_price,
    }

    return sort_columns.get(
        sort_by,
        listing_model.last_seen_at,
    )


async def get_dashboard_row(
    session: AsyncSession, listing_model, marketplace: str
) -> dict[str, Any]:
    today_start = datetime.combine(utc_now().date(), time.min).replace(
        tzinfo=timezone.utc
    )
    tomorrow_start = today_start + timedelta(days=1)
    result = await session.execute(select(func.count(listing_model.id)))
    total_active = int(result.scalar_one() or 0)

    new_today_result = await session.execute(
        select(func.count(listing_model.id)).where(
            listing_model.first_seen_at >= today_start,
            listing_model.first_seen_at < tomorrow_start,
        )
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
        statement = statement.where(
            column >= datetime.combine(date_from, time.min).replace(tzinfo=timezone.utc)
        )
    if date_to:
        statement = statement.where(
            column < datetime.combine(date_to, time.max).replace(tzinfo=timezone.utc)
        )
    return statement


async def list_listings(
    session: AsyncSession,
    marketplace: str,
    page: int,
    page_size: int,
    q: str | None = None,
    status: list[str] | None = None,
    category: list[str] | None = None,
    condition: list[str] | None = None,
    seller: list[str] | None = None,
    currency: list[str] | None = None,
    product_id: str | None = None,
    keyword: str | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    sort_by: str = "last_seen_at",
    sort_order: str = "desc",
):
    config = get_marketplace_config(marketplace)
    listing_model = config["listing"]
    match_model = config["match"]

    if min_price is not None and max_price is not None and min_price > max_price:
        raise ValueError("Min price cannot be greater than max price")

    query = select(listing_model)

    query = apply_listing_filters(
        query,
        listing_model=listing_model,
        match_model=match_model,
        config=config,
        q=q,
        status=status,
        category=category,
        condition=condition,
        seller=seller,
        currency=currency,
        product_id=product_id,
        keyword=keyword,
        min_price=min_price,
        max_price=max_price,
        date_from=date_from,
        date_to=date_to,
    )

    query = query.distinct()

    total_query = select(func.count()).select_from(query.subquery())

    total_result = await session.execute(total_query)
    total = int(total_result.scalar_one() or 0)

    sort_column = get_listing_sort_column(
        listing_model,
        config,
        sort_by,
    )

    if sort_order.lower() == "asc":
        query = query.order_by(
            asc(sort_column).nullslast(),
            asc(listing_model.id),
        )
    else:
        query = query.order_by(
            desc(sort_column).nullslast(),
            desc(listing_model.id),
        )

    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await session.execute(query)

    return list(result.scalars().all()), total


async def get_listing(session: AsyncSession, marketplace: str, listing_id: UUID):
    listing_model = get_marketplace_config(marketplace)["listing"]
    result = await session.execute(
        select(listing_model).where(listing_model.id == listing_id)
    )
    return result.scalar_one_or_none()


async def get_listing_history(
    session: AsyncSession, marketplace: str, listing_id: UUID
):
    snapshot_model = get_marketplace_config(marketplace)["snapshot"]
    result = await session.execute(
        select(snapshot_model)
        .where(snapshot_model.listing_id == listing_id)
        .order_by(snapshot_model.observed_at.desc(), snapshot_model.created_at.desc())
    )
    return list(result.scalars().all())


def apply_listing_filters(
    query,
    *,
    listing_model,
    match_model,
    config,
    q: str | None = None,
    status: list[str] | None = None,
    category: list[str] | None = None,
    condition: list[str] | None = None,
    seller: list[str] | None = None,
    currency: list[str] | None = None,
    product_id: str | None = None,
    keyword: str | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    exclude_fields: set[str] | None = None,
):
    exclude_fields = exclude_fields or set()
    seller_column = get_seller_column(listing_model, config)

    if q and "q" not in exclude_fields:
        query = query.where(listing_model.listing_title.ilike(f"%{q.strip()}%"))

    if status and "status" not in exclude_fields:
        query = query.where(listing_model.listing_status.in_(status))

    if category and "category" not in exclude_fields:
        query = query.where(
            or_(
                listing_model.category_name.in_(category),
                listing_model.category_id.in_(category),
            )
        )

    if condition and "condition" not in exclude_fields:
        query = query.where(
            or_(
                listing_model.condition_name.in_(condition),
                listing_model.condition_id.in_(condition),
            )
        )

    if seller and "seller" not in exclude_fields:
        seller_values = [value for value in seller if value != "__NULL__"]

        seller_conditions = []

        if seller_values:
            seller_conditions.append(seller_column.in_(seller_values))

        if "__NULL__" in seller:
            seller_conditions.append(
                or_(
                    seller_column.is_(None),
                    func.trim(seller_column) == "",
                )
            )

        if seller_conditions:
            query = query.where(or_(*seller_conditions))

    if currency and "currency" not in exclude_fields:
        query = query.where(listing_model.currency.in_(currency))

    needs_match_join = bool(product_id or keyword)

    if needs_match_join:
        query = query.join(
            match_model,
            match_model.listing_id == listing_model.id,
        )

    if product_id and "product_id" not in exclude_fields:
        query = query.join(
            ResearchTarget,
            ResearchTarget.id == match_model.research_target_id,
        ).where(ResearchTarget.product_code == product_id)

    if keyword and "keyword" not in exclude_fields:
        query = query.where(match_model.keyword.ilike(f"%{keyword}%"))

    if min_price is not None and "min_price" not in exclude_fields:
        query = query.where(listing_model.current_price >= min_price)

    if max_price is not None and "max_price" not in exclude_fields:
        query = query.where(listing_model.current_price <= max_price)

    if date_from and "date_from" not in exclude_fields:
        query = query.where(
            listing_model.published_at
            >= datetime.combine(
                date_from,
                time.min,
            ).replace(tzinfo=timezone.utc)
        )

    if date_to and "date_to" not in exclude_fields:
        query = query.where(
            listing_model.published_at
            <= datetime.combine(
                date_to,
                time.max,
            ).replace(tzinfo=timezone.utc)
        )

    return query


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
    result = await session.execute(
        select(SyncError)
        .where(SyncError.sync_job_id == job_id)
        .order_by(SyncError.created_at.asc())
    )
    return list(result.scalars().all())


async def get_facet_rows(
    session: AsyncSession,
    *,
    listing_model,
    match_model,
    config,
    column,
    facet_name: str,
    filters: dict,
    limit: int | None = None,
):
    query = select(
        column.label("value"),
        func.count(distinct(listing_model.id)).label("count"),
    ).select_from(listing_model)

    query = apply_listing_filters(
        query,
        listing_model=listing_model,
        match_model=match_model,
        config=config,
        exclude_fields={facet_name},
        **filters,
    )

    query = query.where(
        column.is_not(None),
        func.trim(column) != "",
    )

    query = query.group_by(column).order_by(asc(column))

    if limit:
        query = query.limit(limit)

    result = await session.execute(query)

    return [
        {
            "value": row.value,
            "label": row.value,
            "count": int(row.count),
        }
        for row in result.all()
    ]


async def get_listing_filter_options(
    session: AsyncSession,
    marketplace: str,
    **filters,
):
    config = get_marketplace_config(marketplace)
    listing_model = config["listing"]
    match_model = config["match"]

    seller_column = get_seller_column(
        listing_model,
        config,
    )

    status = await get_facet_rows(
        session,
        listing_model=listing_model,
        match_model=match_model,
        config=config,
        column=listing_model.listing_status,
        facet_name="status",
        filters=filters,
    )

    category = await get_facet_rows(
        session,
        listing_model=listing_model,
        match_model=match_model,
        config=config,
        column=listing_model.category_name,
        facet_name="category",
        filters=filters,
    )

    condition = await get_facet_rows(
        session,
        listing_model=listing_model,
        match_model=match_model,
        config=config,
        column=listing_model.condition_name,
        facet_name="condition",
        filters=filters,
    )

    seller = await get_facet_rows(
        session,
        listing_model=listing_model,
        match_model=match_model,
        config=config,
        column=seller_column,
        facet_name="seller",
        filters=filters,
        limit=200,
    )

    currency = await get_facet_rows(
        session,
        listing_model=listing_model,
        match_model=match_model,
        config=config,
        column=listing_model.currency,
        facet_name="currency",
        filters=filters,
    )

    price_query = select(
        func.min(listing_model.current_price),
        func.max(listing_model.current_price),
    ).select_from(listing_model)

    price_query = apply_listing_filters(
        price_query,
        listing_model=listing_model,
        match_model=match_model,
        config=config,
        exclude_fields={
            "min_price",
            "max_price",
        },
        **filters,
    )

    price_result = await session.execute(price_query)
    min_price, max_price = price_result.one()

    return {
        "status": status,
        "category": category,
        "condition": condition,
        "seller": seller,
        "currency": currency,
        "price_range": {
            "min": min_price,
            "max": max_price,
        },
    }
