import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import StringForeignKey
from licodex.db.session import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from .thread import Thread

class Message(Base):
    __tablename__ = "message"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    role: Mapped[str] = mapped_column(String(255), unique=True, index=True, default="user")
    content: Mapped[str] = mapped_column(String(32), default="")
    thread_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("thread.id"), nullable=True)
