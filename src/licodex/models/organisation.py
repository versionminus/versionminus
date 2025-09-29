import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, func
from licodex.db.session import Base

class Organisation(Base):
    __tablename__ = "organisations"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Reverse relation to users
    users: Mapped[list["User"]] = relationship("User", back_populates="organisation", cascade="all,delete-orphan")
