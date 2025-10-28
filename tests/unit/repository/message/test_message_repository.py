import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from versionminus.models.user import User
from versionminus.models.thread import Thread
from versionminus.models.message import Message
from versionminus.repositories import message as message_repo

@pytest.mark.asyncio
@pytest.mark.unit
async def test_message_get_and_thread(db_session: AsyncSession):
    u = User(email="msg_unit@example.com")
    db_session.add(u)
    await db_session.flush()
    th = Thread(title="msg-thread", user_id=u.id)
    db_session.add(th)
    await db_session.flush()
    msg = Message(content="payload", thread_id=th.id)
    db_session.add(msg)
    await db_session.flush()
    fetched = await message_repo.get_by_id(db_session, msg.id)
    assert fetched is not None and fetched.id == msg.id
    thr = await message_repo.get_thread(db_session, msg.id)
    assert thr is not None and thr.id == th.id

@pytest.mark.asyncio
@pytest.mark.unit
async def test_message_missing_returns_none(db_session: AsyncSession):
    assert await message_repo.get_by_id(db_session, uuid.uuid4()) is None
