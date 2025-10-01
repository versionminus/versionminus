import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from licodex.repositories import user as user_repo

@pytest.mark.asyncio
@pytest.mark.unit
async def test_user_create_and_get(db_session: AsyncSession):
    user_id = uuid.uuid4()
    created = await user_repo.create(db_session, email="unit_user@example.com", id=user_id)
    assert created.id == user_id
    fetched = await user_repo.get_by_id(db_session, user_id)
    assert fetched is not None and fetched.email == "unit_user@example.com"

@pytest.mark.asyncio
@pytest.mark.unit
async def test_user_list_all(db_session: AsyncSession):
    ids = []
    for e in ["a@u.com", "b@u.com"]:
        u_id = uuid.uuid4()
        ids.append(u_id)
        await user_repo.create(db_session, email=e, id=u_id)
    users = await user_repo.list_all(db_session)
    assert [u.email for u in users] == ["a@u.com", "b@u.com"]
