from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid
from sqlalchemy import JSON

from app.db.base import Base

json_variant = JSON().with_variant(JSONB, "postgresql")


class MarketplaceListingBase:
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_listing_id: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)
    listing_title: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    listing_url: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    listing_location: Mapped[str | None] = mapped_column(Text, nullable=True)
    country_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    condition_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    condition_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True, index=True)
    shipping_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    total_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    currency: Mapped[str | None] = mapped_column(Text, nullable=True)
    listing_views: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    listing_status: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    state_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_payload: Mapped[dict | None] = mapped_column(json_variant, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class ListingMatchBase:
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    research_target_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("hqa_system.research_targets.id", ondelete="CASCADE"), nullable=False, index=True)
    keyword: Mapped[str] = mapped_column(Text, nullable=False)
    match_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    exclude_flag: Mapped[bool] = mapped_column(nullable=False, default=False, server_default="false")
    raw_confidence: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    research_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ListingSnapshotBase:
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    shipping_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    total_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    currency: Mapped[str | None] = mapped_column(Text, nullable=True)
    quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    listing_views: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    listing_status: Mapped[str | None] = mapped_column(Text, nullable=True)
    status_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    state_hash: Mapped[str] = mapped_column(Text, nullable=False)
    raw_payload: Mapped[dict | None] = mapped_column(json_variant, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class SearchRunBase:
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    research_target_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("hqa_system.research_targets.id", ondelete="SET NULL"), nullable=True, index=True)
    keyword: Mapped[str] = mapped_column(Text, nullable=False)
    research_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    api_status: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_results: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    source_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_offset: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_metadata: Mapped[dict | None] = mapped_column(json_variant, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class EbayListing(MarketplaceListingBase, Base):
    __tablename__ = "listings"
    __table_args__ = (
        Index("ix_ebay_listings_title_trgm", "listing_title"),
        {"schema": "ebay"},
    )
    seller_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_status_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    buying_options: Mapped[dict | None] = mapped_column(json_variant, nullable=True)
    status_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class EbayListingMatch(ListingMatchBase, Base):
    __tablename__ = "listing_matches"
    __table_args__ = (UniqueConstraint("listing_id", "research_target_id", "keyword", "research_date", name="uq_ebay_listing_matches_dedupe"), {"schema": "ebay"})


class EbayListingSnapshot(ListingSnapshotBase, Base):
    __tablename__ = "listing_snapshots"
    __table_args__ = ({"schema": "ebay"},)


class EbaySearchRun(SearchRunBase, Base):
    __tablename__ = "search_runs"
    __table_args__ = ({"schema": "ebay"},)


class ReverbListing(MarketplaceListingBase, Base):
    __tablename__ = "listings"
    __table_args__ = (Index("ix_reverb_listings_title_trgm", "listing_title"), {"schema": "reverb"})
    shop_name: Mapped[str | None] = mapped_column(Text, nullable=True)


class ReverbListingMatch(ListingMatchBase, Base):
    __tablename__ = "listing_matches"
    __table_args__ = (UniqueConstraint("listing_id", "research_target_id", "keyword", "research_date", name="uq_reverb_listing_matches_dedupe"), {"schema": "reverb"})


class ReverbListingSnapshot(ListingSnapshotBase, Base):
    __tablename__ = "listing_snapshots"
    __table_args__ = ({"schema": "reverb"},)


class ReverbSearchRun(SearchRunBase, Base):
    __tablename__ = "search_runs"
    __table_args__ = ({"schema": "reverb"},)


class EtsyListing(MarketplaceListingBase, Base):
    __tablename__ = "listings"
    __table_args__ = (Index("ix_etsy_listings_title_trgm", "listing_title"), {"schema": "etsy"})
    shop_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    shop_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    taxonomy_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    etsy_data: Mapped[dict | None] = mapped_column(json_variant, nullable=True)


class EtsyListingMatch(ListingMatchBase, Base):
    __tablename__ = "listing_matches"
    __table_args__ = (UniqueConstraint("listing_id", "research_target_id", "keyword", "research_date", name="uq_etsy_listing_matches_dedupe"), {"schema": "etsy"})


class EtsyListingSnapshot(ListingSnapshotBase, Base):
    __tablename__ = "listing_snapshots"
    __table_args__ = ({"schema": "etsy"},)


class EtsySearchRun(SearchRunBase, Base):
    __tablename__ = "search_runs"
    __table_args__ = ({"schema": "etsy"},)
