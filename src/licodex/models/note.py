import uuid
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, Boolean, Enum, func, ForeignKey
from licodex.db.session import Base
import enum


class NoteStatus(str, enum.Enum):
    """TODO semantics, ERROR means it couldn't be embedded."""
    AVAILABLE = "AVAILABLE"
    ERROR = "ERROR"
    DELETED = "DELETED"


class Note(Base):
    """User note with optional embedding metadata."""

    __tablename__ = "note"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    content: Mapped[str] = mapped_column(String, default="")
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    embedded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    status: Mapped[NoteStatus] = mapped_column(Enum(NoteStatus), default=NoteStatus.AVAILABLE)
    embedded: Mapped[bool] = mapped_column(Boolean, default=False)

    # simple soft-delete helper
    def mark_deleted(self):  # pragma: no cover - convenience method
        self.status = NoteStatus.DELETED
