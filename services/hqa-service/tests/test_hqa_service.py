from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.marketplace import EbayListing, EbayListingMatch
from app.repositories.hqa_repository import list_listings
from app.services.hqa_service import get_marketplace_listings
from app.dependencies.auth import get_current_user_context


@pytest.mark.asyncio
async def test_health_and_ready_endpoints(hqa_test_context):
    client = hqa_test_context["client"]

    health = await client.get("/health")
    ready = await client.get("/ready")

    assert health.status_code == 200
    assert health.json() == {"status": "ok"}
    assert ready.status_code == 200
    assert ready.json() == {"status": "ready"}


@pytest.mark.asyncio
async def test_dashboard_and_listing_filters(hqa_test_context):
    client = hqa_test_context["client"]

    dashboard = await client.get("/api/hqa/dashboard")
    assert dashboard.status_code == 200
    body = dashboard.json()
    assert body["ebay"]["active_listings"] == 3
    assert body["reverb"]["active_listings"] == 1
    assert body["etsy"]["active_listings"] == 1

    listings = await client.get("/api/hqa/ebay/listings", params={"q": "Synth", "page_size": 1, "sort_by": "last_seen_at"})
    assert listings.status_code == 200
    payload = listings.json()
    assert payload["total"] == 2
    assert payload["pages"] == 2
    assert payload["items"][0]["external_listing_id"] in {"ebay|1001", "ebay|1002"}


@pytest.mark.asyncio
async def test_permission_gating_blocks_unauthorized_access(hqa_test_context):
    client = hqa_test_context["client"]
    app = hqa_test_context["app"]
    empty_context = hqa_test_context["empty_context"]

    async def deny_current_user_context():
        return empty_context

    app.dependency_overrides[get_current_user_context] = deny_current_user_context
    response = await client.get("/api/hqa/ebay/listings")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_external_listing_id_pipe_and_duplicate_match_prevention(hqa_test_context):
    sessionmaker = hqa_test_context["sessionmaker"]

    async with sessionmaker() as session:
        result = await session.execute(select(EbayListing).where(EbayListing.external_listing_id == "ebay|1001"))
        listing = result.scalar_one()
        listing_id = listing.id
        assert listing.external_listing_id == "ebay|1001"

        duplicate = EbayListing(
            id=uuid4(),
            external_listing_id="ebay|1001",
            listing_title="Duplicate Listing",
            listing_url="https://example.com/duplicate",
            listing_status="active",
        )
        session.add(duplicate)
        with pytest.raises(IntegrityError):
            await session.commit()
        await session.rollback()

        result = await session.execute(select(EbayListingMatch).where(EbayListingMatch.listing_id == listing_id))
        match = result.scalar_one()
        match_listing_id = match.listing_id
        match_research_target_id = match.research_target_id
        match_keyword = match.keyword
        match_research_date = match.research_date
        duplicate_match = EbayListingMatch(
            listing_id=match_listing_id,
            research_target_id=match_research_target_id,
            keyword=match_keyword,
            match_type=match.match_type,
            exclude_flag=False,
            research_date=match_research_date,
        )
        session.add(duplicate_match)
        with pytest.raises(IntegrityError):
            await session.commit()
        await session.rollback()


@pytest.mark.asyncio
async def test_listing_history_order_and_sync_jobs(hqa_test_context):
    client = hqa_test_context["client"]
    sessionmaker = hqa_test_context["sessionmaker"]

    async with sessionmaker() as session:
        result = await session.execute(select(EbayListing).where(EbayListing.external_listing_id == "ebay|1001"))
        listing = result.scalar_one()
        listing_id = listing.id

    history = await client.get(f"/api/hqa/ebay/listings/{listing_id}/history")
    assert history.status_code == 200
    history_payload = history.json()
    assert history_payload[0]["state_hash"] == "snapshot-new"
    assert history_payload[1]["state_hash"] == "snapshot-old"

    sync_jobs = await client.get("/api/hqa/sync-jobs", params={"marketplace": "ebay"})
    assert sync_jobs.status_code == 200
    assert len(sync_jobs.json()) == 1

    job_id = sync_jobs.json()[0]["id"]
    job_detail = await client.get(f"/api/hqa/sync-jobs/{job_id}")
    assert job_detail.status_code == 200
    assert job_detail.json()["status"] == "success"

    errors = await client.get(f"/api/hqa/sync-jobs/{job_id}/errors")
    assert errors.status_code == 200
    assert errors.json()[0]["error_code"] == "INVALID_PRICE"
