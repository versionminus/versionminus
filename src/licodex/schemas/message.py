import uuid
from pydantic import BaseModel
from .base import ORMBase

class MessageCreate(BaseModel):
    thread_id: uuid.UUID
    content: str = ""
    response: str = ""


class MessageRead(ORMBase):
    id: uuid.UUID
    thread_id: uuid.UUID
    content: str
    response: str


class MessageUpdate(BaseModel):
    content: str | None = None
    response: str | None = None
