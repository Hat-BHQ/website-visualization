from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session_from_app, ping_database

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def ready_check(session: AsyncSession = Depends(get_session_from_app)) -> dict[str, str]:
    await ping_database(session)
    return {"status": "ready"}
