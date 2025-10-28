import uuid
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, ForeignKey, Text, DateTime
from versionminus.db.session import Base
from typing import TYPE_CHECKING

class Message(Base):
    """chat message"""
    __tablename__ = "message"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # Switched from String(255) -> Text to allow large LLM prompts / replies.
    # (Migration 0008_change_message_text.py)
    content: Mapped[str] = mapped_column(Text, default="")
    response: Mapped[str] = mapped_column(Text, default="")
    thread_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("thread.id"), nullable=False)
    # Group identifier referencing a set of Source rows (not a FK because Source.id is non-unique)
    source: Mapped[uuid.UUID | None] = mapped_column(nullable=True, index=True)
    created: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
