import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Literal

class UserCreate(BaseModel):
    email: EmailStr
    role: Literal["user", "admin"] = "user"

class UserRead(BaseModel):
    id: uuid.UUID
    email: EmailStr
    role: str
    created_at: datetime

    class Config:
        from_attributes = True
