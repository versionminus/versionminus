import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from licodex.api import deps
from licodex.schemas.message import MessageCreate, MessageRead, MessageUpdate
from licodex.services.message import (
    create_message as create_message_service,
    get_message_or_404,
    MessageNotFoundError,
    ThreadNotFoundError,
)
from licodex.services.thread import list_messages_per_thread

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("/", response_model=MessageRead, status_code=status.HTTP_201_CREATED,
             summary="Create a message")
async def create_message_route(payload: MessageCreate, session: AsyncSession = Depends(deps.get_db)):
    try:
        # message creation does not contain respose
        # the response is added with the PATCH update
        msg = await create_message_service(
            session,
            thread_id=payload.thread_id,
            content=payload.content,
            source=payload.source,
        )
        await session.commit()
        return msg  # type: ignore
    except ThreadNotFoundError:
        raise HTTPException(status_code=404, detail="Thread not found")


@router.get("/{message_id}", response_model=MessageRead, summary="Get a message")
async def get_message_route(message_id: uuid.UUID, session: AsyncSession = Depends(deps.get_db)):
    try:
        msg = await get_message_or_404(session, message_id)
        return msg  # type: ignore
    except MessageNotFoundError:
        raise HTTPException(status_code=404, detail="Message not found")


@router.get("/thread/{thread_id}", response_model=list[MessageRead], summary="List messages for a thread")
async def list_messages_for_thread_route(thread_id: uuid.UUID, session: AsyncSession = Depends(deps.get_db)):
    rows = await list_messages_per_thread(session, thread_id=thread_id)
    if not rows:
        # If thread id invalid, reuse thread not found semantics
        raise HTTPException(status_code=404, detail="Thread not found")
    # rows is list[(Thread, [Message...])] but filtered to specific thread id -> 0 or 1 element
    return rows[0][1]  # list[Message]


@router.patch("/{message_id}", response_model=MessageRead, summary="Update a message")
async def update_message_route(
    message_id: uuid.UUID, payload: MessageUpdate, session: AsyncSession = Depends(deps.get_db)
):
    try:
        msg = await get_message_or_404(session, message_id)
    except MessageNotFoundError:
        raise HTTPException(status_code=404, detail="Message not found")

    updated = False
    if payload.content is not None and payload.content != msg.content:
        msg.content = payload.content  # type: ignore
        updated = True
    if payload.response is not None and payload.response != msg.response:
        msg.response = payload.response  # type: ignore
        updated = True
    if payload.source is not None and payload.source != msg.source:
        msg.source = payload.source  # type: ignore
        updated = True
    if updated:
        await session.flush()
        await session.commit()
    return msg  # type: ignore


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete a message")
async def delete_message_route(message_id: uuid.UUID, session: AsyncSession = Depends(deps.get_db)):
    try:
        msg = await get_message_or_404(session, message_id)
    except MessageNotFoundError:
        raise HTTPException(status_code=404, detail="Message not found")
    await session.delete(msg)
    await session.commit()
    return None
