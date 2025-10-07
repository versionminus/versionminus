import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Literal, Optional
from .base import ORMBase

class UserCreate(BaseModel):
    # Optional explicit id to allow deterministic user creation in tests/tools.
    # If omitted, server generates a UUID.
    id: Optional[uuid.UUID] = None
    email: EmailStr
    role: Literal["user", "admin"] = "user"

class UserRead(ORMBase):
    id: uuid.UUID
    email: EmailStr
    role: str
    created_at: datetime


class UserEmailUpdate(BaseModel):
    email: EmailStr


