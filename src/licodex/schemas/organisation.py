import uuid
from datetime import datetime
from pydantic import BaseModel
from .base import ORMBase

class OrganisationCreate(BaseModel):
    name: str


class OrganisationRead(ORMBase):
    id: uuid.UUID
    name: str
    created_at: datetime


class OrganisationWithCount(OrganisationRead):
    user_count: int
