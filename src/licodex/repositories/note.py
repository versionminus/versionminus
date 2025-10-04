"""Repository helpers for the Note model."""

import uuid
from typing import Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from licodex.models.note import Note, NoteStatus

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
    note = Note(content=content, user_id=user_id, **({"id": id} if id else {}))
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
    if content is not None:
        note.content = content
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
    await session.flush()
    await session.refresh(note)
    return note
