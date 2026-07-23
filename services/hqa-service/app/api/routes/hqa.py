from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user_context, require_permission
from app.db.session import get_session_from_app
from app.schemas.common import PageResponse
from app.schemas.dashboard import DashboardResponse
from app.schemas.listings import ListingDetailResponse, ListingListItem, ListingSnapshotItem
from app.schemas.sync_jobs import SyncErrorResponse, SyncJobResponse
from app.schemas.sync_trigger import BatchSyncTriggerResponse, SyncTriggerResponse
from app.services.auth_service import CurrentUserContext
from app.services.hqa_service import (
    get_hqa_dashboard,
    get_marketplace_listing,
    get_marketplace_listing_history,
    get_marketplace_listings,
    get_sync_job_details,
    get_sync_job_errors,
    get_sync_jobs,
)
from app.services.sync_service import enqueue_all_marketplaces_sync, enqueue_marketplace_sync

router = APIRouter(prefix="/api/hqa")


def marketplace_permissions() -> dict[str, str]:
    return {
        "ebay": "hqa.ebay.view",
        "reverb": "hqa.reverb.view",
        "etsy": "hqa.etsy.view",
    }


def register_marketplace_routes(marketplace: str) -> None:
    permission = marketplace_permissions()[marketplace]

    async def list_route(
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=30, ge=1, le=100),
        q: str | None = Query(default=None),
        status: str | None = Query(default=None),
        category: str | None = Query(default=None),
        condition: str | None = Query(default=None),
        seller: str | None = Query(default=None),
        product_id: str | None = Query(default=None),
        keyword: str | None = Query(default=None),
        min_price: Decimal | None = Query(default=None),
        max_price: Decimal | None = Query(default=None),
        date_from: date | None = Query(default=None),
        date_to: date | None = Query(default=None),
        sort_by: str | None = Query(default=None),
        sort_order: str = Query(default="desc"),
        session: AsyncSession = Depends(get_session_from_app),
    ) -> PageResponse[ListingListItem]:
        return await get_marketplace_listings(
            session,
            marketplace,
            page,
            page_size,
            q=q,
            status=status,
            category=category,
            condition=condition,
            seller=seller,
            product_id=product_id,
            keyword=keyword,
            min_price=min_price,
            max_price=max_price,
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    async def detail_route(
        id: UUID,
        session: AsyncSession = Depends(get_session_from_app),
    ) -> ListingDetailResponse:
        return await get_marketplace_listing(session, marketplace, id)

    async def history_route(
        id: UUID,
        session: AsyncSession = Depends(get_session_from_app),
    ) -> list[ListingSnapshotItem]:
        return await get_marketplace_listing_history(session, marketplace, id)

    router.add_api_route(
        f"/{marketplace}/listings",
        list_route,
        methods=["GET"],
        response_model=PageResponse[ListingListItem],
        dependencies=[Depends(require_permission(permission, "hqa"))],
        name=f"list_{marketplace}_listings",
    )
    router.add_api_route(
        f"/{marketplace}/listings/{{id}}",
        detail_route,
        methods=["GET"],
        response_model=ListingDetailResponse,
        dependencies=[Depends(require_permission(permission, "hqa"))],
        name=f"get_{marketplace}_listing",
    )
    router.add_api_route(
        f"/{marketplace}/listings/{{id}}/history",
        history_route,
        methods=["GET"],
        response_model=list[ListingSnapshotItem],
        dependencies=[Depends(require_permission(permission, "hqa"))],
        name=f"get_{marketplace}_listing_history",
    )


for marketplace_name in ("ebay", "reverb", "etsy"):
    register_marketplace_routes(marketplace_name)


@router.get("/dashboard", response_model=DashboardResponse, dependencies=[Depends(require_permission("hqa.dashboard.view", "hqa"))])
async def dashboard_route(session: AsyncSession = Depends(get_session_from_app)) -> DashboardResponse:
    return await get_hqa_dashboard(session)


@router.get("/sync-jobs", response_model=list[SyncJobResponse], dependencies=[Depends(require_permission("hqa.sync_history.view", "hqa"))])
async def sync_jobs_route(
    marketplace: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session_from_app),
) -> list[SyncJobResponse]:
    return await get_sync_jobs(session, marketplace)


@router.get("/sync-jobs/{job_id}", response_model=SyncJobResponse, dependencies=[Depends(require_permission("hqa.sync_history.view", "hqa"))])
async def sync_job_detail_route(
    job_id: UUID,
    session: AsyncSession = Depends(get_session_from_app),
) -> SyncJobResponse:
    return await get_sync_job_details(session, job_id)


@router.get("/sync-jobs/{job_id}/errors", response_model=list[SyncErrorResponse], dependencies=[Depends(require_permission("hqa.sync_history.view", "hqa"))])
async def sync_job_errors_route(
    job_id: UUID,
    session: AsyncSession = Depends(get_session_from_app),
) -> list[SyncErrorResponse]:
    return await get_sync_job_errors(session, job_id)


@router.post("/sync", response_model=BatchSyncTriggerResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_all_sync_route(
    session: AsyncSession = Depends(get_session_from_app),
    user: CurrentUserContext = Depends(get_current_user_context),
) -> BatchSyncTriggerResponse:
    return await enqueue_all_marketplaces_sync(session, user, trigger_type="manual")


@router.post("/sync/ebay", response_model=SyncTriggerResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_ebay_sync_route(
    session: AsyncSession = Depends(get_session_from_app),
    user: CurrentUserContext = Depends(get_current_user_context),
) -> SyncTriggerResponse:
    return await enqueue_marketplace_sync(session, user, "ebay", trigger_type="manual")


@router.post("/sync/reverb", response_model=SyncTriggerResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_reverb_sync_route(
    session: AsyncSession = Depends(get_session_from_app),
    user: CurrentUserContext = Depends(get_current_user_context),
) -> SyncTriggerResponse:
    return await enqueue_marketplace_sync(session, user, "reverb", trigger_type="manual")


@router.post("/sync/etsy", response_model=SyncTriggerResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_etsy_sync_route(
    session: AsyncSession = Depends(get_session_from_app),
    user: CurrentUserContext = Depends(get_current_user_context),
) -> SyncTriggerResponse:
    return await enqueue_marketplace_sync(session, user, "etsy", trigger_type="manual")
