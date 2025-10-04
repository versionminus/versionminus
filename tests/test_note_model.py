import pytest
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from licodex.repositories import note as note_repo
from licodex.repositories import user as user_repo


@pytest.mark.asyncio
async def test_create_and_list_notes(db_session: AsyncSession):
    # create a user to own the note
    user = await user_repo.create(db_session, email="note-owner@example.com", id=uuid.uuid4())
    created = await note_repo.create(db_session, user_id=user.id, content="Hello")
    assert created.id is not None
    assert created.user_id == user.id
    listed = await note_repo.list_all(db_session)
    assert any(n.id == created.id for n in listed)
