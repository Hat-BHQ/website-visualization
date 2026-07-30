from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.listings import (
    ListingSortBy,
    ListingSortOrder,
)


class ListingExportFilters(BaseModel):
    """
    Filter sử dụng khi export.

    Không có page/page_size vì mặc định export toàn bộ
    kết quả đang phù hợp với bộ lọc.
    """

    q: str | None = None

    status: list[str] = Field(
        default_factory=list,
    )
    category: list[str] = Field(
        default_factory=list,
    )
    condition: list[str] = Field(
        default_factory=list,
    )
    seller: list[str] = Field(
        default_factory=list,
    )
    currency: list[str] = Field(
        default_factory=list,
    )

    product_id: str | None = None
    keyword: str | None = None

    min_price: Decimal | None = None
    max_price: Decimal | None = None

    date_from: date | None = None
    date_to: date | None = None

    sort_by: ListingSortBy = "last_seen_at"
    sort_order: ListingSortOrder = "desc"


class ListingExportRequest(BaseModel):
    """
    Dữ liệu frontend gửi lên khi user bấm Export.
    """

    format: Literal[
        "xlsx",
        "pdf",
        "google_sheets",
    ]

    # Chỉ cho phép tối đa 30 trường mỗi lần export.
    fields: list[str] = Field(
        min_length=1,
        max_length=30,
    )

    filters: ListingExportFilters = Field(
        default_factory=ListingExportFilters,
    )


class GoogleSheetsExportResponse(BaseModel):
    spreadsheet_id: str
    spreadsheet_url: str
    exported_rows: int
