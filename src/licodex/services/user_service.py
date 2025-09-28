from sqlalchemy.ext.asyncio import AsyncSession
from licodex.schemas.user import UserCreate
from licodex.models.user import User
from licodex.repositories.user_repo import get_by_email

class DuplicateEmailError(Exception):
    pass

async def create_user(session: AsyncSession, data: UserCreate) -> User:
    existing = await get_by_email(session, data.email)
    if existing:
        raise DuplicateEmailError()
    user = User(email=data.email, role=data.role)
    session.add(user)
    await session.flush()  # assign PK
    return user
