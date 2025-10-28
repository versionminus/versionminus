import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from licodex.api import deps
from licodex.services.source import list_sources
from licodex.schemas.source import SourceRead

router = APIRouter(prefix="/sources", tags=["sources"])

@router.get("/{sources_id}", response_model=list[SourceRead], summary="List sources for a retrieval group id")
async def get_sources(sources_id: uuid.UUID, session: AsyncSession = Depends(deps.get_db)):
    rows = await list_sources(session, sources_id)
    if not rows:
        # 404 semantics: group id unknown
        raise HTTPException(status_code=404, detail="No sources found for id")
    return rows  # type: ignore
