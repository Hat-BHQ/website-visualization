from __future__ import annotations

from pathlib import Path

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import Settings
from app.db.base import Base
from app.db.seed import seed
from app.main import create_app


@pytest_asyncio.fixture
async def auth_test_context(tmp_path: Path):
    database_path = tmp_path / "auth-test.db"
    settings = Settings(
        DATABASE_URL=f"sqlite+aiosqlite:///{database_path}",
        JWT_SECRET_KEY="test-access-secret",
        JWT_REFRESH_SECRET_KEY="test-refresh-secret",
        CORS_ORIGINS="http://localhost:5173",
        SEED_DEFAULT_PASSWORD="password",
    )

    engine = create_async_engine(settings.database_url, echo=False, future=True)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    await seed(settings)

    app = create_app(settings)
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield {"client": client, "settings": settings, "engine": engine}

    await engine.dispose()
