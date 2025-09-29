import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional
from typing import Literal
from .organisation import OrganisationRead
from .base import ORMBase

class UserCreate(BaseModel):
    email: EmailStr
    role: Literal["user", "admin"] = "user"

class UserRead(ORMBase):
    id: uuid.UUID
    email: EmailStr
    role: str
    created_at: datetime


class UserEmailUpdate(BaseModel):
    email: EmailStr


class UserWithOrganisationRead(UserRead):
    organisation: Optional[OrganisationRead] = None

