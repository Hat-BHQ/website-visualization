from __future__ import annotations

from datetime import datetime

from app.schemas.common import ORMBaseModel


class MarketplaceDashboard(ORMBaseModel):
    active_listings: int
    new_today: int
    last_sync_at: datetime | None
    sync_status: str | None


class DashboardResponse(ORMBaseModel):
    ebay: MarketplaceDashboard
    reverb: MarketplaceDashboard
    etsy: MarketplaceDashboard
