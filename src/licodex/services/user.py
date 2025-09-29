from sqlalchemy.ext.asyncio import AsyncSession
from licodex.schemas.user import UserCreate
from licodex.models.user import User
from licodex.repositories.user import get_by_email, get_by_id, list_all, list_all_with_org_join
from licodex.services.organisation import get_organisation_or_404, OrganisationNotFoundError
import uuid

class UserNotFoundError(Exception):
    pass

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


async def get_user_or_404(session: AsyncSession, user_id: uuid.UUID) -> User:
    user = await get_by_id(session, user_id)
    if not user:
        raise UserNotFoundError()
    return user


async def delete_user(session: AsyncSession, user_id: uuid.UUID) -> None:
    user = await get_user_or_404(session, user_id)
    await session.delete(user)  # type: ignore


async def update_user_email(session: AsyncSession, user_id: uuid.UUID, new_email: str) -> User:
    user = await get_user_or_404(session, user_id)
    # If unchanged, just return early
    if user.email == new_email:
        return user
    existing = await get_by_email(session, new_email)
    if existing:
        raise DuplicateEmailError()
    user.email = new_email  # type: ignore
    await session.flush()
    return user


async def list_users(session: AsyncSession) -> list[User]:
    return await list_all(session)


async def list_users_detailed(session: AsyncSession, organisation_id=None):  # type: ignore
    rows = await list_all_with_org_join(session, organisation_id=organisation_id)
    return rows


async def assign_user_organisation(session: AsyncSession, user_id: uuid.UUID, organisation_id: uuid.UUID) -> User:
    user = await get_user_or_404(session, user_id)
    # ensure organisation exists
    org = await get_organisation_or_404(session, organisation_id)
    # Set the relationship itself so it's already present on the instance and no
    # lazy load is required later (avoids MissingGreenlet in async contexts).
    user.organisation = org  # type: ignore[attr-defined]
    await session.flush()
    return user

