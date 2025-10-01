import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from licodex.api import deps
from licodex.schemas.thread import ThreadCreate, ThreadRead, ThreadUpdate
from licodex.schemas.message import MessageRead
from licodex.services.thread import (
    create_thread,
    get_thread_or_404,
    ThreadNotFoundError,
    list_message_counts,
    list_messages_per_thread,
)

router = APIRouter(prefix="/threads", tags=["threads"])


@router.post("/", response_model=ThreadRead, status_code=status.HTTP_201_CREATED,
             summary="Create a thread")
async def create_thread_route(payload: ThreadCreate, session: AsyncSession = Depends(deps.get_db)):
    thread = await create_thread(session, title=payload.title, user_id=payload.user_id)
    await session.commit()
    return thread  # type: ignore


@router.get("/{thread_id}", response_model=ThreadRead, summary="Get a thread")
async def get_thread_route(thread_id: uuid.UUID, session: AsyncSession = Depends(deps.get_db)):
    try:
        thread = await get_thread_or_404(session, thread_id)
        return thread  # type: ignore
    except ThreadNotFoundError:
        raise HTTPException(status_code=404, detail="Thread not found")


@router.get("/", response_model=list[ThreadRead], summary="List threads")
async def list_threads_route(session: AsyncSession = Depends(deps.get_db)):
    # Re-use list_message_counts to get threads; ignore counts for now.
    rows = await list_message_counts(session)
    return [t for (t, _count) in rows]


@router.get("/{thread_id}/messages", response_model=list[MessageRead],
            summary="List messages in a thread")
async def list_messages_in_thread_route(thread_id: uuid.UUID, session: AsyncSession = Depends(deps.get_db)):
    rows = await list_messages_per_thread(session, thread_id=thread_id)
    if not rows:
        # Thread does not exist
        raise HTTPException(status_code=404, detail="Thread not found")
    # rows[0] -> (Thread, [Message, ...])
    return rows[0][1]


@router.patch("/{thread_id}", response_model=ThreadRead, summary="Update a thread")
async def update_thread_route(
    thread_id: uuid.UUID, payload: ThreadUpdate, session: AsyncSession = Depends(deps.get_db)
):
    try:
        thread = await get_thread_or_404(session, thread_id)
    except ThreadNotFoundError:
        raise HTTPException(status_code=404, detail="Thread not found")

    updated = False
    if payload.title is not None and payload.title != thread.title:
        thread.title = payload.title  # type: ignore
        updated = True

    if updated:
        await session.flush()
        await session.commit()
    return thread  # type: ignore


@router.delete("/{thread_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete a thread")
async def delete_thread_route(thread_id: uuid.UUID, session: AsyncSession = Depends(deps.get_db)):
    try:
        thread = await get_thread_or_404(session, thread_id)
    except ThreadNotFoundError:
        raise HTTPException(status_code=404, detail="Thread not found")
    await session.delete(thread)
    await session.commit()
    return None
