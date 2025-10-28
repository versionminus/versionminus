"""Repository helpers for the Message model.

This module was previously (mis)used for User repository helpers; those have been
relocated to ``licodex.repositories.user``. It now provides message-centric
queries only.
"""

import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from licodex.models.message import Message
from licodex.models.thread import Thread

__all__ = [
    "get_by_id",
    "get_thread",
    "create",
]


async def get_by_id(session: AsyncSession, message_id: uuid.UUID) -> Optional[Message]:
    """Return a Message by id or None if it does not exist."""
    res = await session.execute(select(Message).where(Message.id == message_id))
    return res.scalar_one_or_none()


async def get_thread(session: AsyncSession, message_id: uuid.UUID) -> Optional[Thread]:
    """Return the Thread that owns the given message id.

    Returns None if the message (or its thread) does not exist. Executes a single
    joined query limited to 1 row.
    """
    stmt = (
        select(Thread)
        .join(Message, Message.thread_id == Thread.id)
        .where(Message.id == message_id)
        .limit(1)
    )
    res = await session.execute(stmt)
    return res.scalar_one_or_none()


async def create(
    session: AsyncSession,
    *,
    thread_id: uuid.UUID,
    content: str = "",
    response: str = "",
    id: uuid.UUID | None = None,
    source: uuid.UUID | None = None,
) -> Message:
    """Create a new Message.

    Parameters:
        session: active AsyncSession.
        thread_id: owning thread UUID (must exist or hit FK constraint on flush).
        content: user-provided content.
        response: optional assistant/system response.
        id: optional explicit UUID.
        source: optional retrieval source group id.

    Returns the persisted Message (flushed, not committed).
    """
    message = Message(
        thread_id=thread_id,
        content=content,
        response=response,
        source=source,
        **({"id": id} if id else {})
    )
    session.add(message)
    await session.flush()
    return message
