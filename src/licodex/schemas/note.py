import uuid
from datetime import datetime
from pydantic import BaseModel
from .base import ORMBase
from licodex.models.note import NoteStatus


class NoteCreate(BaseModel):
    content: str = ""
    user_id: uuid.UUID


class NoteRead(ORMBase):
    id: uuid.UUID
    content: str
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    embedded_at: datetime | None
    status: NoteStatus
    embedded: bool


class NoteUpdate(BaseModel):
    content: str | None = None
    embedded: bool | None = None
    status: NoteStatus | None = None
    embedded_at: datetime | None = None
