import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from licodex.models.user import User
from licodex.models.thread import Thread
from licodex.models.message import Message

from licodex.repositories import user as user_repo
from licodex.repositories import thread as thread_repo
from licodex.repositories import message as message_repo

@pytest.mark.asyncio
@pytest.mark.integration
async def test_user_repository_crud(db_session: AsyncSession):
	u_id = uuid.uuid4()
	user = await user_repo.create(db_session, email="repo@example.com", id=u_id)
	assert user.id == u_id
	fetched = await user_repo.get_by_id(db_session, u_id)
	assert fetched is not None
	assert fetched.email == "repo@example.com"
	all_users = await user_repo.list_all(db_session)
	assert len(all_users) == 1

@pytest.mark.asyncio
@pytest.mark.integration
async def test_thread_repository_listing(db_session: AsyncSession):
	u = User(email="t@example.com")
	db_session.add(u)
	await db_session.flush()
	th = Thread(title="thread-1", user_id=u.id)
	db_session.add(th)
	await db_session.flush()
	m1 = Message(content="hello", thread_id=th.id)
	m2 = Message(content="world", thread_id=th.id)
	db_session.add_all([m1, m2])
	await db_session.flush()
	fetched_thread = await thread_repo.get_by_id(db_session, th.id)
	assert fetched_thread is not None
	owner = await thread_repo.get_user(db_session, th.id)
	assert owner is not None and owner.id == u.id
	listed = await thread_repo.list_messages_per_thread(db_session, th.id)
	assert len(listed) == 1
	t_obj, msgs = listed[0]
	assert t_obj.id == th.id
	assert {m.content for m in msgs} == {"hello", "world"}
	counts = await thread_repo.list_message_counts(db_session)
	assert counts and counts[0][0].id == th.id and counts[0][1] == 2

@pytest.mark.asyncio
@pytest.mark.integration
async def test_message_repository_getters(db_session: AsyncSession):
	u = User(email="m@example.com")
	db_session.add(u)
	await db_session.flush()
	th = Thread(title="thread-m", user_id=u.id)
	db_session.add(th)
	await db_session.flush()
	msg = Message(content="payload", thread_id=th.id)
	db_session.add(msg)
	await db_session.flush()
	fetched_msg = await message_repo.get_by_id(db_session, msg.id)
	assert fetched_msg is not None and fetched_msg.id == msg.id
	fetched_thread = await message_repo.get_thread(db_session, msg.id)
	assert fetched_thread is not None and fetched_thread.id == th.id
	random_id = uuid.uuid4()
	assert await message_repo.get_by_id(db_session, random_id) is None
	assert await message_repo.get_thread(db_session, random_id) is None
