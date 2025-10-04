import uuid
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, Boolean, Enum, func, ForeignKey
from licodex.db.session import Base
import enum

class IdeaStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    DELETED = "DELETED"


class Idea(Base):
    """Idea expressed in multiple notes."""

    __tablename__ = "idea"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), default="", index=True)
    relationship_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    note_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("notes.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    status: Mapped[IdeaStatus] = mapped_column(Enum(IdeaStatus), default=IdeaStatus.AVAILABLE)
    embedded: Mapped[bool] = mapped_column(Boolean, default=False)

    # simple soft-delete helper
    def mark_deleted(self):  # pragma: no cover - convenience method
        self.status = IdeaStatus.DELETED
