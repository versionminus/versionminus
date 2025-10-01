"""User service layer.

Provides higher-level operations around the `User` repository, enforcing
business rules (like email uniqueness) and raising domain-specific
exceptions instead of returning ``None``.
"""
from __future__ import annotations

import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from licodex.schemas.user import UserCreate
from licodex.models.user import User
from licodex.repositories.user import (
    get_by_id as repo_get_by_id,
    list_all as repo_list_all,
)

__all__ = [
    "UserNotFoundError",
    "DuplicateEmailError",
    "create_user",
    "get_user_or_404",
    "delete_user",
    "update_user_email",
    "list_users",
]

class UserNotFoundError(Exception):
    """Raised when a user id does not correspond to a stored record."""

class DuplicateEmailError(Exception):
    """Raised when attempting to create/update a user with an existing email."""

async def _email_exists(session: AsyncSession, email: str) -> bool:
    stmt = select(User.id).where(User.email == email).limit(1)
    res = await session.execute(stmt)
    return res.scalar_one_or_none() is not None

async def create_user(session: AsyncSession, data: UserCreate) -> User:
    if await _email_exists(session, data.email):
        raise DuplicateEmailError()
    user = User(email=data.email, role=data.role)
    session.add(user)
    await session.flush()
    return user

async def get_user_or_404(session: AsyncSession, user_id: uuid.UUID) -> User:
    user = await repo_get_by_id(session, user_id)
    if not user:
        raise UserNotFoundError()
    return user

async def delete_user(session: AsyncSession, user_id: uuid.UUID) -> None:
    user = await get_user_or_404(session, user_id)
    await session.delete(user)  # type: ignore[arg-type]

async def update_user_email(session: AsyncSession, user_id: uuid.UUID, new_email: str) -> User:
    user = await get_user_or_404(session, user_id)
    if user.email == new_email:
        return user
    if await _email_exists(session, new_email):
        raise DuplicateEmailError()
    user.email = new_email  # type: ignore[assignment]
    await session.flush()
    return user

async def list_users(session: AsyncSession) -> list[User]:
    return await repo_list_all(session)
