import uuid
from typing import Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from licodex.models.source import Source

__all__ = [
    "create_many",
    "list_by_group_id",
]

async def create_many(session: AsyncSession, *, sources_id: uuid.UUID, rows: Sequence[tuple[uuid.UUID, str]]):
    """Bulk create Source rows for a retrieval event.

    Parameters:
        session: active session
        sources_id: identifier shared across created rows
        rows: iterable of (note_id, quote) pairs
    Returns list[Source]
    """
    created: list[Source] = []
    for note_id, quote in rows:
        src = Source(id=sources_id, note_id=note_id, quote=quote)
        session.add(src)
        created.append(src)
    await session.flush()
    return created

async def list_by_group_id(session: AsyncSession, sources_id: uuid.UUID) -> list[Source]:
    res = await session.execute(select(Source).where(Source.id == sources_id))
    return list(res.scalars().all())
