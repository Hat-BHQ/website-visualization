from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.dependencies.auth import get_current_user_context
from app.core.config import Settings
from app.db.base import Base
from app.db.session import create_engine
from app.main import create_app
from app.models.marketplace import EtsyListing, EbayListing, EbayListingMatch, EbayListingSnapshot, ReverbListing
from app.models.system import ResearchTarget, SyncError, SyncJob
from app.schemas.auth import UserModule
from app.services.auth_service import CurrentUserContext


async def seed_hqa_data(sessionmaker: async_sessionmaker):
    now = datetime.now(timezone.utc)
    yesterday = now - timedelta(days=1)
    two_days_ago = now - timedelta(days=2)

    async with sessionmaker() as session:
        target = ResearchTarget(product_code="PROD-1", brand="Roland", model="Juno-106", target_category="synth")
        session.add(target)
        await session.flush()

        ebay_a = EbayListing(
            id=uuid4(),
            external_listing_id="ebay|1001",
            listing_title="Vintage Synth A",
            listing_url="https://example.com/ebay/1001",
            seller_name="ShopOne",
            published_at=yesterday,
            listing_location="Berlin",
            country_code="DE",
            category_id="cat-a",
            category_name="Synths",
            condition_id="used",
            condition_name="Used",
            image_url="https://example.com/a.jpg",
            current_price=Decimal("199.99"),
            shipping_price=Decimal("19.99"),
            total_price=Decimal("219.98"),
            currency="USD",
            listing_status="active",
            first_seen_at=two_days_ago,
            last_seen_at=now,
            state_hash="hash-ebay-a",
        )
        ebay_b = EbayListing(
            id=uuid4(),
            external_listing_id="ebay|1002",
            listing_title="Vintage Synth B",
            listing_url="https://example.com/ebay/1002",
            seller_name="ShopTwo",
            published_at=yesterday,
            listing_location="Paris",
            country_code="FR",
            category_id="cat-a",
            category_name="Synths",
            condition_id="used",
            condition_name="Used",
            image_url="https://example.com/b.jpg",
            current_price=Decimal("299.99"),
            shipping_price=Decimal("29.99"),
            total_price=Decimal("329.98"),
            currency="USD",
            listing_status="active",
            first_seen_at=yesterday,
            last_seen_at=now,
            state_hash="hash-ebay-b",
        )
        ebay_c = EbayListing(
            id=uuid4(),
            external_listing_id="ebay|1003",
            listing_title="Keyboard Rack",
            listing_url="https://example.com/ebay/1003",
            seller_name="ShopThree",
            published_at=yesterday,
            listing_location="Rome",
            country_code="IT",
            category_id="cat-b",
            category_name="Accessories",
            condition_id="new",
            condition_name="New",
            image_url="https://example.com/c.jpg",
            current_price=Decimal("99.99"),
            shipping_price=Decimal("9.99"),
            total_price=Decimal("109.98"),
            currency="USD",
            listing_status="active",
            first_seen_at=yesterday,
            last_seen_at=now,
            state_hash="hash-ebay-c",
        )
        reverb_listing = ReverbListing(
            id=uuid4(),
            external_listing_id="reverb|2001",
            listing_title="Reverb Synth",
            listing_url="https://example.com/reverb/2001",
            shop_name="ReverbShop",
            published_at=yesterday,
            listing_location="London",
            country_code="GB",
            category_id="cat-r",
            category_name="Synths",
            condition_id="used",
            condition_name="Used",
            image_url="https://example.com/r.jpg",
            current_price=Decimal("399.99"),
            shipping_price=Decimal("39.99"),
            total_price=Decimal("439.98"),
            currency="USD",
            listing_status="active",
            first_seen_at=yesterday,
            last_seen_at=now,
            state_hash="hash-reverb",
        )
        etsy_listing = EtsyListing(
            id=uuid4(),
            external_listing_id="etsy|3001",
            listing_title="Etsy Handmade Synth Knob",
            listing_url="https://example.com/etsy/3001",
            shop_id="shop-1",
            shop_name="EtsyShop",
            taxonomy_id="tax-1",
            etsy_data={"handmade": True},
            published_at=yesterday,
            listing_location="Madrid",
            country_code="ES",
            category_id="cat-e",
            category_name="Accessories",
            condition_id="new",
            condition_name="New",
            image_url="https://example.com/e.jpg",
            current_price=Decimal("29.99"),
            shipping_price=Decimal("4.99"),
            total_price=Decimal("34.98"),
            currency="USD",
            listing_status="active",
            first_seen_at=yesterday,
            last_seen_at=now,
            state_hash="hash-etsy",
        )

        session.add_all([ebay_a, ebay_b, ebay_c, reverb_listing, etsy_listing])
        await session.flush()

        session.add_all(
            [
                EbayListingMatch(
                    listing_id=ebay_a.id,
                    research_target_id=target.id,
                    keyword="synth",
                    match_type="keyword",
                    exclude_flag=False,
                    raw_confidence=Decimal("0.9500"),
                    research_date=yesterday.date(),
                ),
                EbayListingMatch(
                    listing_id=ebay_b.id,
                    research_target_id=target.id,
                    keyword="synth",
                    match_type="keyword",
                    exclude_flag=False,
                    raw_confidence=Decimal("0.9000"),
                    research_date=yesterday.date(),
                ),
            ]
        )
        session.add_all(
            [
                EbayListingSnapshot(listing_id=ebay_a.id, observed_at=two_days_ago, state_hash="snapshot-old", price=Decimal("189.99"), currency="USD"),
                EbayListingSnapshot(listing_id=ebay_a.id, observed_at=yesterday, state_hash="snapshot-new", price=Decimal("199.99"), currency="USD"),
            ]
        )
        job = SyncJob(
            id=uuid4(),
            marketplace="ebay",
            trigger_type="manual",
            status="success",
            completed_at=now,
            total_source_rows=3,
            inserted_rows=2,
            updated_rows=1,
            unchanged_rows=0,
            skipped_rows=0,
            error_rows=1,
            error_summary="1 row failed",
            requested_by_user_id=None,
        )
        session.add(job)
        await session.flush()
        session.add(
            SyncError(
                sync_job_id=job.id,
                marketplace="ebay",
                source_sheet="Listings",
                source_row_number=4,
                external_listing_id="ebay|bad-row",
                processing_stage="transform",
                error_code="INVALID_PRICE",
                error_message="Invalid price format",
                raw_row={"price": "oops"},
            )
        )
        await session.commit()


@pytest_asyncio.fixture
async def hqa_test_context(tmp_path: Path):
    database_path = tmp_path / "hqa-test.db"
    settings = Settings(
        DATABASE_URL=f"sqlite+aiosqlite:///{database_path}",
        JWT_SECRET_KEY="test-access-secret",
        CORS_ORIGINS="http://localhost:5173",
    )
    engine = create_engine(settings)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    await seed_hqa_data(sessionmaker)

    app = create_app(settings)
    allowed_context = CurrentUserContext(
        id=uuid4(),
        email="admin@example.com",
        full_name="HQA Admin",
        is_superadmin=False,
        modules=[
            UserModule(
                code="hqa",
                name="HQA",
                role="admin",
                frontend_path="/hqa",
                permissions=[
                    "hqa.dashboard.view",
                    "hqa.ebay.view",
                    "hqa.reverb.view",
                    "hqa.etsy.view",
                    "hqa.sync_history.view",
                    "hqa.ebay.sync",
                    "hqa.reverb.sync",
                    "hqa.etsy.sync",
                ],
            )
        ],
    )
    empty_context = CurrentUserContext(
        id=uuid4(),
        email="viewer@example.com",
        full_name="Viewer",
        is_superadmin=False,
        modules=[],
    )

    async def allow_current_user_context():
        return allowed_context

    app.dependency_overrides[get_current_user_context] = allow_current_user_context
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield {
                "app": app,
                "client": client,
                "engine": engine,
                "sessionmaker": sessionmaker,
                "settings": settings,
                "allowed_context": allowed_context,
                "empty_context": empty_context,
            }

    app.dependency_overrides.clear()
    await engine.dispose()
