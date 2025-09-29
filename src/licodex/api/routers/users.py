import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from licodex.api import deps
from licodex.schemas.user import UserCreate, UserRead, UserEmailUpdate, UserWithOrganisationRead
from licodex.services.user import (
    create_user,
    delete_user,
    update_user_email,
    list_users,
    list_users_detailed,
    assign_user_organisation,
    DuplicateEmailError,
    UserNotFoundError,
    OrganisationNotFoundError,
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


@router.get("/detailed", response_model=list[UserWithOrganisationRead], summary="List users with organisation",
            description="List users including their organisation (if any). Optionally filter by organisation_id.")
async def list_users_detailed_route(organisation_id: uuid.UUID | None = None, session: AsyncSession = Depends(deps.get_db)):
    rows = await list_users_detailed(session, organisation_id=organisation_id)
    # Map (User, Organisation|None) -> schema
    out: list[UserWithOrganisationRead] = []
    for user, org in rows:
        out.append(UserWithOrganisationRead(
            id=user.id,
            email=user.email,
            role=user.role,
            created_at=user.created_at,
            organisation=(None if not org else org)
        ))
    return out


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


@router.patch("/{user_id}/organisation/{organisation_id}", response_model=UserWithOrganisationRead,
              summary="Assign user to organisation",
              description="Associate a user with an organisation by ID.")
async def assign_user_organisation_route(
    user_id: uuid.UUID,
    organisation_id: uuid.UUID,
    session: AsyncSession = Depends(deps.get_db),
):
    try:
        user = await assign_user_organisation(session, user_id, organisation_id)
        await session.commit()
        # Relationship set eagerly in service; model config from_attributes allows direct return
        return UserWithOrganisationRead(
            id=user.id,
            email=user.email,
            role=user.role,
            created_at=user.created_at,
            organisation=user.organisation,  # already populated, no lazy load
        )
    except UserNotFoundError:
        raise HTTPException(status_code=404, detail="User not found")
    except OrganisationNotFoundError:
        raise HTTPException(status_code=404, detail="Organisation not found")

