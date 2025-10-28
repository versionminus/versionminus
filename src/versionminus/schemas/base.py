from pydantic import BaseModel, ConfigDict

class ORMBase(BaseModel):
    """Base schema enabling attribute (ORM) population for Pydantic v2 models.

    Inherit from this class for any read/response schema that will be constructed
    directly from ORM / domain objects rather than plain dicts.
    """
    model_config = ConfigDict(from_attributes=True)
