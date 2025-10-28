from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from versionminus.api import deps
from versionminus.services.health import check_db

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/liveness")
async def liveness():
    """Verify whether the API is ready to receive traffic."""
    return {"status": "ok"}

@router.get("/readiness")
async def readiness(session: AsyncSession = Depends(deps.get_db)):
    """Verify whether the API is ready to process traffic."""
    if await check_db(session):
        return {"status": "ready"}
    return {"status": "degraded"}
