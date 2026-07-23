from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from app.dependencies.auth import get_current_user_context
from app.models.marketplace import EbayListing, EbayListingSnapshot
from app.models.system import SyncJob
from app.schemas.auth import UserModule
from app.services.auth_service import CurrentUserContext
from app.sync import pipeline as sync_pipeline
from app.sync.pipeline import LOCK_KEYS, run_marketplace_sync
from app.worker.celery_app import celery_app


class FakeRedis:
    def __init__(self):
        self.store: dict[str, str] = {}

    def set(self, key, value, nx=False, ex=None):
        if nx and key in self.store:
            return False
        self.store[key] = value
        return True

    def get(self, key):
        return self.store.get(key)

    def eval(self, script, numkeys, key, owner):
        if self.store.get(key) == owner:
            self.store.pop(key, None)
            return 1
        return 0


def _ebay_rows(price: str = "199.99") -> list[dict[str, str]]:
    return [
        {
            "external_listing_id": "98819971.0",
            "listing_title": "Roland Synth",
            "listing_url": "https://example.com/item/98819971",
            "seller_name": "Seller One",
            "published_date": "45500",
            "research_date": "45500",
            "product_code": "PROD-SYNC-1",
            "keyword": "roland",
            "current_price": price,
            "shipping_price": "10.00",
            "listing_status": "active",
            "currency": "USD",
        }
    ]


@pytest.mark.asyncio
async def test_sync_idempotent_and_snapshot_on_change(hqa_test_context, monkeypatch):
    settings = hqa_test_context["settings"]
    sessionmaker = hqa_test_context["sessionmaker"]

    fake_redis = FakeRedis()
    monkeypatch.setattr(sync_pipeline, "create_redis_client", lambda url: fake_redis)
    monkeypatch.setattr(sync_pipeline, "read_sheet_rows", lambda spreadsheet_id, service_account_file, sheet_name: _ebay_rows("199.99"))

    first = await run_marketplace_sync("ebay", trigger_type="manual", settings=settings)
    second = await run_marketplace_sync("ebay", trigger_type="manual", settings=settings)
    assert first["status"] == "success"
    assert second["status"] == "success"

    async with sessionmaker() as session:
        listing_count_result = await session.execute(
            select(func.count(EbayListing.id)).where(EbayListing.external_listing_id == "98819971")
        )
        listing_count = listing_count_result.scalar_one()
        assert listing_count == 1

        snapshot_count_result = await session.execute(
            select(func.count(EbayListingSnapshot.id)).join(
                EbayListing, EbayListing.id == EbayListingSnapshot.listing_id
            ).where(EbayListing.external_listing_id == "98819971")
        )
        snapshot_count = snapshot_count_result.scalar_one()
        assert snapshot_count == 1

    monkeypatch.setattr(sync_pipeline, "read_sheet_rows", lambda spreadsheet_id, service_account_file, sheet_name: _ebay_rows("249.99"))
    third = await run_marketplace_sync("ebay", trigger_type="manual", settings=settings)
    assert third["status"] == "success"

    async with sessionmaker() as session:
        snapshot_count_result = await session.execute(
            select(func.count(EbayListingSnapshot.id)).join(
                EbayListing, EbayListing.id == EbayListingSnapshot.listing_id
            ).where(EbayListing.external_listing_id == "98819971")
        )
        snapshot_count = snapshot_count_result.scalar_one()
        assert snapshot_count == 2


@pytest.mark.asyncio
async def test_redis_lock_blocks_duplicate_job(hqa_test_context, monkeypatch):
    client = hqa_test_context["client"]
    sessionmaker = hqa_test_context["sessionmaker"]

    from app.services import sync_service

    fake_redis = FakeRedis()
    fake_redis.store[LOCK_KEYS["ebay"]] = "active-owner"
    monkeypatch.setattr(sync_service, "create_redis_client", lambda url: fake_redis)

    async with sessionmaker() as session:
        running_job = SyncJob(
            id=uuid4(),
            marketplace="ebay",
            trigger_type="manual",
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        session.add(running_job)
        await session.commit()

    response = await client.post("/api/hqa/sync/ebay")
    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["marketplace"] == "ebay"


@pytest.mark.asyncio
async def test_user_without_permission_gets_403(hqa_test_context):
    client = hqa_test_context["client"]
    app = hqa_test_context["app"]

    no_sync_user = CurrentUserContext(
        id=uuid4(),
        email="nosync@example.com",
        full_name="No Sync",
        is_superadmin=False,
        modules=[
            UserModule(
                code="hqa",
                name="HQA",
                role="viewer",
                frontend_path="/hqa",
                permissions=["hqa.ebay.view"],
            )
        ],
    )

    async def denied_user():
        return no_sync_user

    app.dependency_overrides[get_current_user_context] = denied_user
    response = await client.post("/api/hqa/sync/ebay")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_gets_202_for_sync_enqueue(hqa_test_context, monkeypatch):
    client = hqa_test_context["client"]

    from app.services import sync_service

    fake_redis = FakeRedis()
    monkeypatch.setattr(sync_service, "create_redis_client", lambda url: fake_redis)

    class DummyTask:
        @staticmethod
        def delay(**kwargs):
            return None

    monkeypatch.setitem(sync_service.SYNC_TASKS, "ebay", DummyTask)

    response = await client.post("/api/hqa/sync/ebay")
    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "queued"
    assert body["marketplace"] == "ebay"


def test_scheduler_timezone_and_times():
    assert celery_app.conf.timezone == "Asia/Bangkok"
    schedule = celery_app.conf.beat_schedule
    assert schedule["sync-ebay-0800"]["schedule"]._orig_minute == 0
    assert schedule["sync-ebay-0800"]["schedule"]._orig_hour == 8
    assert schedule["sync-reverb-0805"]["schedule"]._orig_minute == 5
    assert schedule["sync-reverb-0805"]["schedule"]._orig_hour == 8
    assert schedule["sync-etsy-0810"]["schedule"]._orig_minute == 10
    assert schedule["sync-etsy-0810"]["schedule"]._orig_hour == 8
