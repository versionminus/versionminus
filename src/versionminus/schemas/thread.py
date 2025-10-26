import uuid
from datetime import datetime
from pydantic import BaseModel
from .base import ORMBase

class ThreadCreate(BaseModel):
    title: str
    user_id: uuid.UUID


class ThreadRead(ORMBase):
    id: uuid.UUID
    title: str
    user_id: uuid.UUID


class ThreadUpdate(BaseModel):
    title: str | None = None
