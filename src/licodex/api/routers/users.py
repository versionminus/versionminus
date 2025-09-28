from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from licodex.db.session import get_db
from licodex.schemas.user import UserCreate, UserRead
from licodex.services.user_service import create_user, DuplicateEmailError

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(payload: UserCreate, session: AsyncSession = Depends(get_db)):
    try:
        user = await create_user(session, payload)
        await session.commit()
        return user
    except DuplicateEmailError:
        raise HTTPException(status_code=409, detail="Email already registered")
