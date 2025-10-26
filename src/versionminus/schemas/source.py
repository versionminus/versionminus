import uuid
from pydantic import BaseModel
from .base import ORMBase

class SourceRead(ORMBase):
    id: uuid.UUID  # retrieval group id
    note_id: uuid.UUID
    quote: str
    distance: float | None = None

class SourceGroupRead(BaseModel):
    sources_id: uuid.UUID
    sources: list[SourceRead]
