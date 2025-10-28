"""Service helpers for thread and message domain logic.

Adds higher-level operations on top of repository helpers such as
creation with simple validation and not-found error mapping.
"""

import uuid
from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from versionminus.repositories import thread as thread_repo
from versionminus.repositories import message as message_repo
from versionminus.models.thread import Thread
from versionminus.models.message import Message
from versionminus.models.user import User

__all__ = [
    "ThreadNotFoundError",
    "MessageNotFoundError",
    "create_thread",
    "create_message",
    "get_thread_or_404",
    "get_message_or_404",
    "get_thread_user",
    "list_messages_per_thread",
    "list_message_counts",
]


class ThreadNotFoundError(Exception):
    pass


class MessageNotFoundError(Exception):
    pass


async def create_thread(
    session: AsyncSession, *, title: str, user_id: uuid.UUID, id: uuid.UUID | None = None
) -> Thread:
    # Rely on DB unique constraint for title; could pre-check if desired.
    thread = await thread_repo.create(session, title=title, user_id=user_id, id=id)
    return thread


async def create_message(
    session: AsyncSession,
    *,
    thread_id: uuid.UUID,
    content: str = "",
    response: str = "",
    id: uuid.UUID | None = None,
) -> Message:
    # ensure thread exists to surface clearer error than FK failure
    if not await thread_repo.get_by_id(session, thread_id):
        raise ThreadNotFoundError()
    msg = await message_repo.create(
        session,
        thread_id=thread_id,
        content=content,
        response=response,
        id=id,
    )
    return msg


async def get_thread_or_404(session: AsyncSession, thread_id: uuid.UUID) -> Thread:
    thread = await thread_repo.get_by_id(session, thread_id)
    if not thread:
        raise ThreadNotFoundError()
    return thread


async def get_message_or_404(session: AsyncSession, message_id: uuid.UUID) -> Message:
    msg = await message_repo.get_by_id(session, message_id)
    if not msg:
        raise MessageNotFoundError()
    return msg


async def get_thread_user(session: AsyncSession, thread_id: uuid.UUID) -> User | None:
    return await thread_repo.get_user(session, thread_id)


# passthrough list helpers (re-exported for clarity)
list_messages_per_thread = thread_repo.list_messages_per_thread
list_message_counts = thread_repo.list_message_counts


