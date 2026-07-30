from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

ListingSortBy = Literal[
    "last_seen_at",
    "published_at",
    "status",
    "category",
    "condition",
    "seller",
    "price",
]

ListingSortOrder = Literal["asc", "desc"]


class ListingListRequest(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=30, ge=1, le=100)

    q: str | None = None

    status: list[str] | None = None
    category: list[str] | None = None
    condition: list[str] | None = None
    seller: list[str] | None = None
    currency: list[str] | None = None

    product_id: str | None = None
    keyword: str | None = None

    min_price: Decimal | None = None
    max_price: Decimal | None = None

    date_from: date | None = None
    date_to: date | None = None

    sort_by: ListingSortBy = "last_seen_at"
    sort_order: ListingSortOrder = "desc"


class ListingFacetOption(BaseModel):
    value: str
    label: str
    count: int


class ListingPriceRange(BaseModel):
    min: Decimal | None = None
    max: Decimal | None = None


class ListingFilterOptionsResponse(BaseModel):
    status: list[ListingFacetOption]
    category: list[ListingFacetOption]
    condition: list[ListingFacetOption]
    seller: list[ListingFacetOption]
    currency: list[ListingFacetOption]
    price_range: ListingPriceRange


class ListingListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    external_listing_id: str
    listing_title: str
    listing_url: str
    seller_name: str | None = None
    shop_name: str | None = None
    shop_id: str | None = None
    published_at: datetime | None = None
    listing_location: str | None = None
    country_code: str | None = None
    category_id: str | None = None
    category_name: str | None = None
    condition_id: str | None = None
    condition_name: str | None = None
    image_url: str | None = None
    current_price: Decimal | None = None
    shipping_price: Decimal | None = None
    total_price: Decimal | None = None
    currency: str | None = None
    quantity: int | None = None
    listing_views: int | None = None
    listing_status: str
    status_reason: str | None = None
    first_seen_at: datetime
    last_seen_at: datetime
    state_hash: str | None = None


class ListingDetailResponse(ListingListItem):
    raw_payload: dict | None = None
    buying_options: dict | None = None
    etsy_data: dict | None = None


class ListingSnapshotItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    listing_id: UUID
    observed_at: datetime
    price: Decimal | None = None
    shipping_price: Decimal | None = None
    total_price: Decimal | None = None
    currency: str | None = None
    quantity: int | None = None
    listing_views: int | None = None
    listing_status: str | None = None
    status_reason: str | None = None
    state_hash: str
    raw_payload: dict | None = None
    created_at: datetime
