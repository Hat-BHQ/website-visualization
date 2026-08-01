from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


DailyReportTableKey = Literal[
    "all",
    "table_1",
    "table_2",
    "table_3",
    "table_4",
    "table_5",
    "table_6",
    "table_7",
    "table_8",
]

DailyReportSort = Literal[
    "last_updated_desc",
    "newest_collected",  # backward compatibility for older frontend bundles
    "price_desc",
    "price_asc",
    "title_asc",
]


class DailyReportSummary(BaseModel):
    total_listings_on_selected_date: int
    new_listings_qualified: int
    ended_listings: int
    out_of_stock: int


class DailyReportTableCount(BaseModel):
    key: DailyReportTableKey
    label: str
    count: int


class DailyReportStatusOption(BaseModel):
    value: str
    label: str
    count: int


class DailyReportItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    external_listing_id: str
    listing_title: str
    listing_url: str

    seller_name: str | None = None
    shop_name: str | None = None

    category_name: str | None = None
    condition_name: str | None = None

    current_price: Decimal | None = None
    shipping_price: Decimal | None = None
    total_price: Decimal | None = None
    currency: str | None = None

    image_url: str | None = None
    listing_status: str
    status_reason: str | None = None

    published_at: datetime | None = None
    first_seen_at: datetime
    last_seen_at: datetime

    # The timestamp used to place the listing into a daily report.
    # It is last_seen_at, falling back to first_seen_at.
    report_at: datetime
    report_date: date


class DailyReportResponse(BaseModel):
    marketplace: Literal[
        "ebay",
        "reverb",
        "etsy",
    ]
    selected_date: date | None

    summary: DailyReportSummary
    status_options: list[DailyReportStatusOption]
    table_counts: list[DailyReportTableCount]

    items: list[DailyReportItem]

    page: int
    page_size: int
    total: int
    pages: int
