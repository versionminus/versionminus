import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from licodex.repositories import note as note_repo


@pytest.mark.asyncio
async def test_create_and_list_notes(db_session: AsyncSession):
    created = await note_repo.create(db_session, title="Test Note", content="Hello")
    assert created.id is not None
    listed = await note_repo.list_all(db_session)
    assert any(n.id == created.id for n in listed)
