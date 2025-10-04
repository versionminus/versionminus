import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from licodex.api import deps
from licodex.schemas.note import NoteCreate, NoteRead, NoteUpdate
from licodex.services.note import (
    create_note,
    get_note_or_404,
    list_notes,
    update_note,
    delete_note,
    NoteNotFoundError,
)

router = APIRouter(prefix="/notes", tags=["notes"])


@router.post(
    "/",
    response_model=NoteRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a note",
)
async def create_note_route(
    payload: NoteCreate, session: AsyncSession = Depends(deps.get_db)
):
    note = await create_note(session, title=payload.title, content=payload.content)
    await session.commit()
    return note  # type: ignore


@router.get(
    "/{note_id}", response_model=NoteRead, summary="Get a note"
)
async def get_note_route(
    note_id: uuid.UUID, session: AsyncSession = Depends(deps.get_db)
):
    try:
        note = await get_note_or_404(session, note_id)
        return note  # type: ignore
    except NoteNotFoundError:
        raise HTTPException(status_code=404, detail="Note not found")


@router.get(
    "/", response_model=list[NoteRead], summary="List notes"
)
async def list_notes_route(
    include_deleted: bool = Query(False, description="Include soft-deleted notes"),
    session: AsyncSession = Depends(deps.get_db),
):
    return await list_notes(session, include_deleted=include_deleted)  # type: ignore


@router.patch(
    "/{note_id}", response_model=NoteRead, summary="Update a note"
)
async def update_note_route(
    note_id: uuid.UUID,
    payload: NoteUpdate,
    session: AsyncSession = Depends(deps.get_db),
):
    try:
        note = await update_note(
            session,
            note_id,
            title=payload.title,
            content=payload.content,
            embedded=payload.embedded,
            status=payload.status,
            embedded_at=payload.embedded_at,
        )
        await session.commit()
        return note  # type: ignore
    except NoteNotFoundError:
        raise HTTPException(status_code=404, detail="Note not found")


@router.delete(
    "/{note_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete (soft) a note"
)
async def delete_note_route(
    note_id: uuid.UUID, session: AsyncSession = Depends(deps.get_db)
):
    try:
        await delete_note(session, note_id)
        await session.commit()
    except NoteNotFoundError:
        raise HTTPException(status_code=404, detail="Note not found")
    return None
