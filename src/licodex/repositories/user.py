from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from licodex.models.organisation import Organisation
from licodex.models.user import User
from typing import Optional

async def get_by_email(session: AsyncSession, email: str) -> Optional[User]:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_by_id(session: AsyncSession, user_id) -> Optional[User]:  # type: ignore
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def list_all(session: AsyncSession) -> list[User]:
    result = await session.execute(select(User).order_by(User.created_at))
    return list(result.scalars().all())


async def list_all_with_org_join(session: AsyncSession, organisation_id=None) -> list[tuple[User, Organisation | None]]:  # type: ignore
    stmt = (
        select(User, Organisation)
        .outerjoin(Organisation, User.organisation_id == Organisation.id)
        .order_by(User.created_at)
    )
    if organisation_id:
        stmt = stmt.where(User.organisation_id == organisation_id)
    res = await session.execute(stmt)
    return [(row[0], row[1]) for row in res.all()]

