import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from licodex.db.session import get_db
from licodex.schemas.user import UserCreate, UserRead, UserEmailUpdate
from licodex.endpoints.user.create import create_user_endpoint
from licodex.services.user_service import (
    delete_user,
    update_user_email,
    list_users,
    DuplicateEmailError,
    UserNotFoundError,
)

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user_route(payload: UserCreate, session: AsyncSession = Depends(get_db)):
    return await create_user_endpoint(payload, session)


@router.get("/", response_model=list[UserRead])
async def list_users_route(session: AsyncSession = Depends(get_db)):
    return await list_users(session)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_route(user_id: uuid.UUID, session: AsyncSession = Depends(get_db)):
    try:
        await delete_user(session, user_id)
        await session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except UserNotFoundError:
        raise HTTPException(status_code=404, detail="User not found")


@router.patch("/{user_id}/email", response_model=UserRead)
async def update_user_email_route(
    user_id: uuid.UUID,
    payload: UserEmailUpdate,
    session: AsyncSession = Depends(get_db),
):
    try:
        user = await update_user_email(session, user_id, payload.email)
        await session.commit()
        return user
    except UserNotFoundError:
        raise HTTPException(status_code=404, detail="User not found")
    except DuplicateEmailError:
        raise HTTPException(status_code=409, detail="Email already registered")

