"""Message service layer.

Encapsulates higher-level operations on messages beyond raw repository
helpers. Keeps message-related errors domain-specific.
"""
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from licodex.models.message import Message
from licodex.models.thread import Thread
from licodex.repositories import message as message_repo
from licodex.repositories import thread as thread_repo

__all__ = [
    "MessageNotFoundError",
    "ThreadNotFoundError",
    "create_message",
    "get_message_or_404",
    "get_message_thread",
]

class MessageNotFoundError(Exception):
    pass

class ThreadNotFoundError(Exception):
    pass

async def create_message(
    session: AsyncSession,
    *,
    thread_id: uuid.UUID,
    content: str = "",
    response: str = "",
    id: uuid.UUID | None = None,
    source: uuid.UUID | None = None,
) -> Message:
    # Validate parent thread existence for clearer error semantics
    if not await thread_repo.get_by_id(session, thread_id):
        raise ThreadNotFoundError()
    msg = await message_repo.create(
        session,
        thread_id=thread_id,
        content=content,
        response=response,
        id=id,
        source=source,
    )
    return msg

async def get_message_or_404(session: AsyncSession, message_id: uuid.UUID) -> Message:
    msg = await message_repo.get_by_id(session, message_id)
    if not msg:
        raise MessageNotFoundError()
    return msg

async def get_message_thread(session: AsyncSession, message_id: uuid.UUID) -> Thread | None:
    return await message_repo.get_thread(session, message_id)

