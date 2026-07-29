from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.hqa_repository import (
    get_dashboard,
    get_listing,
    get_listing_filter_options,
    get_listing_history,
    get_sync_job,
    list_listings,
    list_sync_errors,
    list_sync_jobs,
)

from app.schemas.common import PageResponse
from app.schemas.dashboard import DashboardResponse, MarketplaceDashboard
from app.schemas.listings import (
    ListingDetailResponse,
    ListingListItem,
    ListingSnapshotItem,
)
from app.schemas.sync_jobs import SyncErrorResponse, SyncJobResponse


async def get_hqa_dashboard(session: AsyncSession) -> DashboardResponse:
    dashboard = await get_dashboard(session)
    return DashboardResponse(
        ebay=MarketplaceDashboard(**dashboard["ebay"]),
        reverb=MarketplaceDashboard(**dashboard["reverb"]),
        etsy=MarketplaceDashboard(**dashboard["etsy"]),
    )


async def get_marketplace_filter_options(
    session: AsyncSession,
    marketplace: str,
    **filters,
):
    return await get_listing_filter_options(
        session,
        marketplace,
        **filters,
    )


async def get_marketplace_listings(
    session: AsyncSession,
    marketplace: str,
    page: int,
    page_size: int,
    **filters,
) -> PageResponse[ListingListItem]:
    try:
        items, total = await list_listings(
            session,
            marketplace,
            page,
            page_size,
            **filters,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    pages = (total + page_size - 1) // page_size if total else 0

    return PageResponse[ListingListItem](
        items=[ListingListItem.model_validate(item) for item in items],
        page=page,
        page_size=page_size,
        total=total,
        pages=pages,
    )


async def get_marketplace_listing(
    session: AsyncSession, marketplace: str, listing_id: UUID
) -> ListingDetailResponse:
    listing = await get_listing(session, marketplace, listing_id)
    if listing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found"
        )
    return ListingDetailResponse.model_validate(listing)


async def get_marketplace_listing_history(
    session: AsyncSession, marketplace: str, listing_id: UUID
) -> list[ListingSnapshotItem]:
    snapshots = await get_listing_history(session, marketplace, listing_id)
    return [ListingSnapshotItem.model_validate(snapshot) for snapshot in snapshots]


async def get_sync_jobs(
    session: AsyncSession, marketplace: str | None = None
) -> list[SyncJobResponse]:
    jobs = await list_sync_jobs(session, marketplace)
    return [SyncJobResponse.model_validate(job) for job in jobs]


async def get_sync_job_details(session: AsyncSession, job_id: UUID) -> SyncJobResponse:
    job = await get_sync_job(session, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sync job not found"
        )
    return SyncJobResponse.model_validate(job)


async def get_sync_job_errors(
    session: AsyncSession, job_id: UUID
) -> list[SyncErrorResponse]:
    errors = await list_sync_errors(session, job_id)
    return [SyncErrorResponse.model_validate(error) for error in errors]
