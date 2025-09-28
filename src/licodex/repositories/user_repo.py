from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from licodex.models.user import User
from typing import Optional

async def get_by_email(session: AsyncSession, email: str) -> Optional[User]:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()
