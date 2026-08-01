from __future__ import annotations

from datetime import date

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.daily_report_repository import (
    get_daily_report_data,
)
from app.reporting.daily_report_rules import (
    REPORT_TABLE_KEYS,
)
from app.schemas.daily_report import (
    DailyReportResponse,
)


VALID_SORTS = {
    "last_updated_desc",
    "newest_collected",
    "price_desc",
    "price_asc",
    "title_asc",
}


async def get_marketplace_daily_report(
    session: AsyncSession,
    *,
    marketplace: str,
    selected_date: date | None,
    status_filter: list[str] | None,
    table_key: str,
    sort_by: str,
    page: int,
    page_size: int,
) -> DailyReportResponse:
    if table_key not in REPORT_TABLE_KEYS:
        raise HTTPException(
            status_code=422,
            detail="Daily report table is invalid.",
        )

    if sort_by not in VALID_SORTS:
        raise HTTPException(
            status_code=422,
            detail="Daily report sort is invalid.",
        )

    data = await get_daily_report_data(
        session,
        marketplace=marketplace,
        selected_date=selected_date,
        status_filter=status_filter,
        table_key=table_key,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
    )

    return DailyReportResponse(**data)
