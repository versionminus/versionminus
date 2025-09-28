from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from licodex.db.session import get_db
from licodex.services.health_service import check_db

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/liveness")
async def liveness():
    return {"status": "ok"}

@router.get("/readiness")
async def readiness(session: AsyncSession = Depends(get_db)):
    if await check_db(session):
        return {"status": "ready"}
    return {"status": "degraded"}
