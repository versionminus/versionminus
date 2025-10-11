import uuid
from datetime import datetime
from pydantic import BaseModel
from .base import ORMBase

class MessageCreate(BaseModel):
    thread_id: uuid.UUID
    content: str = ""
    response: str = ""
    source: uuid.UUID | None = None


class MessageRead(ORMBase):
    id: uuid.UUID
    thread_id: uuid.UUID
    content: str
    response: str
    source: uuid.UUID | None = None
    created: datetime


class MessageUpdate(BaseModel):
    content: str | None = None
    response: str | None = None
    source: uuid.UUID | None = None
