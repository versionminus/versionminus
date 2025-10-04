import uuid
from datetime import datetime
from pydantic import BaseModel
from .base import ORMBase
from licodex.models.note import NoteStatus


class NoteCreate(BaseModel):
    title: str = ""
    content: str = ""


class NoteRead(ORMBase):
    id: uuid.UUID
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
    embedded_at: datetime | None
    status: NoteStatus
    embedded: bool


class NoteUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    embedded: bool | None = None
    status: NoteStatus | None = None
    embedded_at: datetime | None = None
