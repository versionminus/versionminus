from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from licodex.models.organisation import Organisation
from licodex.models.user import User

async def get_by_name(session: AsyncSession, name: str) -> Optional[Organisation]:
    res = await session.execute(select(Organisation).where(Organisation.name == name))
    return res.scalar_one_or_none()

async def get_by_id(session: AsyncSession, org_id) -> Optional[Organisation]:  # type: ignore
    res = await session.execute(select(Organisation).where(Organisation.id == org_id))
    return res.scalar_one_or_none()

async def create(session: AsyncSession, name: str) -> Organisation:
    org = Organisation(name=name)
    session.add(org)
    await session.flush()
    return org

async def list_all(session: AsyncSession) -> list[Organisation]:
    res = await session.execute(select(Organisation).order_by(Organisation.created_at))
    return list(res.scalars().all())

async def list_with_counts(session: AsyncSession) -> list[tuple[Organisation, int]]:
    stmt = (
        select(Organisation, func.count(User.id).label("user_count"))
        .outerjoin(User, User.organisation_id == Organisation.id)
        .group_by(Organisation.id)
        .order_by(Organisation.created_at)
    )
    res = await session.execute(stmt)
    return [(row[0], row[1]) for row in res.all()]
