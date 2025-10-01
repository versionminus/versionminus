import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from licodex.models.user import User
from licodex.models.thread import Thread
from licodex.repositories import message as message_repo

@pytest.mark.asyncio
@pytest.mark.unit
async def test_message_create(db_session: AsyncSession):
    u = User(email="msg_create@example.com")
    db_session.add(u)
    await db_session.flush()
    th = Thread(title="msg-create-thread", user_id=u.id)
    db_session.add(th)
    await db_session.flush()
    m_id = uuid.uuid4()
    msg = await message_repo.create(db_session, thread_id=th.id, content="hello", response="world", id=m_id)
    assert msg.id == m_id and msg.content == "hello" and msg.response == "world"
    fetched = await message_repo.get_by_id(db_session, m_id)
    assert fetched is not None and fetched.thread_id == th.id
