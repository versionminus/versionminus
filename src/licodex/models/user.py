import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, func
from licodex.db.session import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    role: Mapped[str] = mapped_column(String(32), default="user")
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
