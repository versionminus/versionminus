import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from versionminus.models.user import User

async def get_by_id(session: AsyncSession, id: uuid.UUID) -> Optional[User]:
    res = await session.execute(select(User).where(User.id == id))
    return res.scalar_one_or_none()

async def create(session: AsyncSession, email: str, id: uuid.UUID) -> User:
    user = User(email=email, id=id)
    session.add(user)
    await session.flush()
    return user

async def list_all(session: AsyncSession) -> list[User]:
    res = await session.execute(select(User).order_by(User.created_at))
    return list(res.scalars().all())

