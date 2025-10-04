"""Note service layer.

Provides higher-level operations around the `Note` repository and raises
domain-specific exceptions instead of returning ``None``.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from licodex.models.note import Note, NoteStatus
from licodex.repositories import note as note_repo

__all__ = [
    "NoteNotFoundError",
    "create_note",
    "get_note_or_404",
    "list_notes",
    "update_note",
    "delete_note",
]


class NoteNotFoundError(Exception):
    pass


async def create_note(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    content: str = "",
    id: uuid.UUID | None = None,
) -> Note:
    note = await note_repo.create(session, user_id=user_id, content=content, id=id)
    return note


async def get_note_or_404(session: AsyncSession, note_id: uuid.UUID) -> Note:
    note = await note_repo.get_by_id(session, note_id)
    if not note:
        raise NoteNotFoundError()
    return note


async def list_notes(session: AsyncSession, include_deleted: bool = False) -> list[Note]:
    return list(await note_repo.list_all(session, include_deleted=include_deleted))


async def update_note(
    session: AsyncSession,
    note_id: uuid.UUID,
    *,
    content: str | None = None,
    embedded: bool | None = None,
    status: NoteStatus | None = None,
    embedded_at: datetime | None = None,
) -> Note:
    note = await get_note_or_404(session, note_id)
    note = await note_repo.update(
        session,
        note,
        content=content,
        embedded=embedded,
        status=status,
        embedded_at=embedded_at,
    )
    return note


async def delete_note(session: AsyncSession, note_id: uuid.UUID) -> None:
    note = await get_note_or_404(session, note_id)
    await note_repo.soft_delete(session, note)
