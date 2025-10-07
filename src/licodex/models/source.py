import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, ForeignKey, Text
from licodex.db.session import Base

class Source(Base):
    """Retrieved quote used to ground a chat response.

    A logical retrieval event (for a single user message) is identified by the
    shared ``id`` value across one or more Source rows. The ``id`` column is
    intentionally *not* the table primary key to allow many rows to share the
    same identifier. A surrogate primary key ``pk`` is provided for ORM needs.
    """
    __tablename__ = "source"
    pk: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # Retrieval grouping identifier (e.g. copied onto Message.source)
    id: Mapped[uuid.UUID] = mapped_column(index=True)
    note_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("note.id"), nullable=False, index=True)
    quote: Mapped[str] = mapped_column(Text, default="")
