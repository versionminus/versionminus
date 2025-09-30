import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, ForeignKey
from licodex.db.session import Base
from typing import TYPE_CHECKING

class Message(Base):
    """chat message"""
    __tablename__ = "message"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    content: Mapped[str] = mapped_column(String(255), default="")
    response: Mapped[str] = mapped_column(String(255), default="")
    thread_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("thread.id"), nullable=False)
