import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from licodex.models.user import User
from licodex.models.thread import Thread
from licodex.models.message import Message
from licodex.repositories import thread as thread_repo

@pytest.mark.asyncio
@pytest.mark.unit
async def test_thread_get_and_user(db_session: AsyncSession):
    u = User(email="thread_unit@example.com")
    db_session.add(u)
    await db_session.flush()
    th = Thread(title="t-unit", user_id=u.id)
    db_session.add(th)
    await db_session.flush()
    fetched = await thread_repo.get_by_id(db_session, th.id)
    assert fetched is not None
    owner = await thread_repo.get_user(db_session, th.id)
    assert owner is not None and owner.id == u.id

@pytest.mark.asyncio
@pytest.mark.unit
async def test_thread_message_listing_and_counts(db_session: AsyncSession):
    u = User(email="thread_unit2@example.com")
    db_session.add(u)
    await db_session.flush()
    th = Thread(title="t-unit-2", user_id=u.id)
    db_session.add(th)
    await db_session.flush()
    m1 = Message(content="x", thread_id=th.id)
    m2 = Message(content="y", thread_id=th.id)
    db_session.add_all([m1, m2])
    await db_session.flush()
    per = await thread_repo.list_messages_per_thread(db_session, th.id)
    assert len(per) == 1
    _, msgs = per[0]
    assert {m.content for m in msgs} == {"x", "y"}
    counts = await thread_repo.list_message_counts(db_session)
    mapping = {t.id: c for t, c in counts}
    assert mapping[th.id] == 2
