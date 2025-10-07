"""Service layer for retrieval sources."""
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from licodex.repositories import source as source_repo
from licodex.repositories import note as note_repo

__all__ = [
    "create_sources_for_group",
    "retrieve_relevant_notes_stub",
    "list_sources",
]

async def create_sources_for_group(session: AsyncSession, *, sources_id: uuid.UUID, items: list[tuple[uuid.UUID, str]]):
    return await source_repo.create_many(session, sources_id=sources_id, rows=items)

async def list_sources(session: AsyncSession, sources_id: uuid.UUID):
    return await source_repo.list_by_group_id(session, sources_id)

async def retrieve_relevant_notes_stub(session: AsyncSession, *, user_query: str, limit: int = 3) -> list[tuple[uuid.UUID, str]]:
    """Naive retrieval implementation.

    Until a real vector similarity pipeline is wired, we fall back to a
    substring search over notes to pick "relevant" quotes. This keeps the API
    contract stable for the frontend while development continues.
    Returns list of (note_id, quote) pairs.
    """
    # Fetch all notes (could be optimized). For brevity reuse repository directly.
    from sqlalchemy import select
    from licodex.models.note import Note
    res = await session.execute(select(Note))
    candidates = list(res.scalars().all())
    user_lower = user_query.lower()
    scored: list[tuple[float, tuple[uuid.UUID, str]]] = []
    for n in candidates:
        content_lower = n.content.lower()
        if user_lower in content_lower:
            # Simple score: shorter distance from start
            idx = content_lower.index(user_lower)
            score = 1.0 / (1 + idx)
            snippet = n.content[max(0, idx-40): idx+len(user_query)+80]
            scored.append((score, (n.id, snippet.strip())))
    scored.sort(key=lambda x: x[0], reverse=True)
    top = [pair for _score, pair in scored[:limit]]
    # If not enough matches, just take first notes
    if len(top) < limit:
        for n in candidates:
            if n.id not in {nid for nid, _ in top}:
                top.append((n.id, n.content[:120]))
            if len(top) >= limit:
                break
    return top[:limit]
