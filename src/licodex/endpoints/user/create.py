import uuid
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from licodex.db.session import get_db
from licodex.schemas.user import UserCreate, UserRead
from licodex.services.user_service import create_user, DuplicateEmailError


async def create_user_endpoint(
    payload: UserCreate,
    session: AsyncSession = Depends(get_db),
) -> UserRead:
    """Create a new user.

    Raises 409 if email already exists.
    """
    try:
        user = await create_user(session, payload)
        await session.commit()
        return user  # type: ignore
    except DuplicateEmailError:
        # Let FastAPI turn into JSON response
        raise HTTPException(status_code=409, detail="Email already registered")
