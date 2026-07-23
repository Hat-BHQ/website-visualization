from fastapi import APIRouter

router = APIRouter(prefix="/api/hqs")


@router.get("/dashboard")
async def dashboard() -> dict[str, str]:
    return {"module": "HQS", "status": "ok"}
