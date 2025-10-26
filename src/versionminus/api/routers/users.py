import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from versionminus.api import deps
from versionminus.schemas.user import UserCreate, UserRead, UserEmailUpdate
from versionminus.services.user import (
    create_user,
    delete_user,
    update_user_email,
    list_users,
    DuplicateEmailError,
    UserNotFoundError,
)

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED,
             summary="Create a user",
             description="Create a new user with the provided email and role. Email must be unique.")
async def create_user_route(payload: UserCreate, session: AsyncSession = Depends(deps.get_db)):
    try:
        user = await create_user(session, payload)
        await session.commit()
        return user  # type: ignore
    except DuplicateEmailError:
        # Let FastAPI turn into JSON response
        raise HTTPException(status_code=409, detail="Email already registered")


@router.get("/", response_model=list[UserRead], summary="List users",
            description="List all users in creation order (no join).")
async def list_users_route(session: AsyncSession = Depends(deps.get_db)):
    return await list_users(session)


"""User routes (organisation functionality removed)."""


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_route(user_id: uuid.UUID, session: AsyncSession = Depends(deps.get_db)):
    try:
        await delete_user(session, user_id)
        await session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except UserNotFoundError:
        raise HTTPException(status_code=404, detail="User not found")


@router.patch("/{user_id}/email", response_model=UserRead,
              summary="Update user email",
              description="Change a user's email address. Fails if new email already exists.")
async def update_user_email_route(
    user_id: uuid.UUID,
    payload: UserEmailUpdate,
    session: AsyncSession = Depends(deps.get_db),
):
    try:
        user = await update_user_email(session, user_id, payload.email)
        await session.commit()
        return user
    except UserNotFoundError:
        raise HTTPException(status_code=404, detail="User not found")
    except DuplicateEmailError:
        raise HTTPException(status_code=409, detail="Email already registered")



