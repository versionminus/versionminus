import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from versionminus.models.user import User
from versionminus.repositories import thread as thread_repo

@pytest.mark.asyncio
@pytest.mark.unit
async def test_thread_create(db_session: AsyncSession):
    # create owning user first
    u = User(email="thread_create@example.com")
    db_session.add(u)
    await db_session.flush()
    t_id = uuid.uuid4()
    thread = await thread_repo.create(db_session, title="created-thread", user_id=u.id, id=t_id)
    assert thread.id == t_id
    fetched = await thread_repo.get_by_id(db_session, t_id)
    assert fetched is not None and fetched.title == "created-thread"
