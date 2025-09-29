import uuid
from datetime import datetime
from pydantic import BaseModel

class OrganisationCreate(BaseModel):
    name: str

class OrganisationRead(BaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime

    class Config:
        from_attributes = True

class OrganisationWithCount(OrganisationRead):
    user_count: int
