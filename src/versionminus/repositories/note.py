"""Repository helpers for the Note model."""

import uuid
from typing import Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from versionminus.models.note import Note, NoteStatus

__all__ = [
    "get_by_id",
    "list_all",
    "create",
    "update",
    "soft_delete",
]


async def get_by_id(session: AsyncSession, note_id: uuid.UUID) -> Optional[Note]:
    res = await session.execute(select(Note).where(Note.id == note_id))
    return res.scalar_one_or_none()


async def list_all(session: AsyncSession, include_deleted: bool = False) -> Sequence[Note]:
    stmt = select(Note)
    if not include_deleted:
        stmt = stmt.where(Note.status != NoteStatus.DELETED)
    res = await session.execute(stmt.order_by(Note.created_at))
    return list(res.scalars().all())


async def create(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    content: str = "",
    id: uuid.UUID | None = None,
) -> Note:
    # New notes always start unembedded
    note = Note(content=content, user_id=user_id, embedded=False, embedded_at=None, **({"id": id} if id else {}))
    session.add(note)
    # Flush so INSERT is issued and server defaults (timestamps, etc.) are populated,
    # then refresh to eagerly load them. Without this, accessing attributes like
    # updated_at during Pydantic serialization can trigger a lazy load which in
    # async SQLAlchemy raises MissingGreenlet.
    await session.flush()
    await session.refresh(note)
    return note


async def update(
    session: AsyncSession,
    note: Note,
    *,
    content: str | None = None,
    embedded: bool | None = None,
    status: NoteStatus | None = None,
    embedded_at=None,
) -> Note:
    content_changed = content is not None and content != note.content
    if content is not None:
        note.content = content
    # Any content update should reset embedding status unless explicitly overridden and delete old embeddings from Milvus
    if content_changed and embedded is None:
        # Best-effort Milvus deletion so re-embedding generates fresh vectors
        try:  # pragma: no cover - external system
            from versionminus.core.milvus.milvus import get_milvus
            from pymilvus import Collection, utility
            get_milvus()
            if utility.has_collection("notes"):
                coll = Collection("notes")
                coll.delete(expr=f"note_id == '{note.id}'")
        except Exception:
            pass
        note.embedded = False
        note.embedded_at = None
    if embedded is not None:
        note.embedded = embedded
    if status is not None:
        note.status = status
    if embedded_at is not None:
        note.embedded_at = embedded_at
    await session.flush()
    await session.refresh(note)
    return note


async def soft_delete(session: AsyncSession, note: Note) -> Note:
    note.status = NoteStatus.DELETED
    # Mark embedding metadata as removed locally (even if Milvus deletion fails)
    note.embedded = False
    note.embedded_at = None
    # Also remove any embeddings for this note from Milvus if available
    try:  # pragma: no cover - external system
        from versionminus.core.milvus.milvus import get_milvus
        from pymilvus import Collection, utility
        get_milvus()
        if utility.has_collection("notes"):
            coll = Collection("notes")
            # delete by scalar field expression
            # note_id stored as string UUID
            coll.delete(expr=f"note_id == '{note.id}'")
    except Exception:
        pass
    await session.flush()
    await session.refresh(note)
    return note
