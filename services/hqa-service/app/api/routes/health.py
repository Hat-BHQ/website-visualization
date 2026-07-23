from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session_from_app

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def ready_check(session: AsyncSession = Depends(get_session_from_app)) -> dict[str, str]:
    await session.execute(text("SELECT 1"))
    return {"status": "ready"}
