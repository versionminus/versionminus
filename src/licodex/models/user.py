import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, func, ForeignKey
from datetime import datetime
from licodex.db.session import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from .organisation import Organisation

class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    role: Mapped[str] = mapped_column(String(32), default="user")
    # Use datetime for created_at
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    organisation_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("organisations.id"), nullable=True)

    # Relationship
    # Forward reference inside string; optional relationship
    organisation: Mapped["Organisation | None"] = relationship(back_populates="users")
