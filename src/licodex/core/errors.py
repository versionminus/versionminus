"""Project-wide custom exceptions.

This module centralizes domain-specific exception types so that routers and
services can raise / catch them without importing deep infrastructure errors
like ``asyncpg`` or raw SQLAlchemy exceptions.

Add new errors here rather than scattering small ``class XError(Exception):``
definitions across the codebase; this keeps the public error surface easy to
audit and map to HTTP responses.
"""
from __future__ import annotations

class LicodexError(Exception):
    """Base class for all custom project exceptions.

    Subclass this rather than ``Exception`` directly for new domain errors.
    """


class ResponseTooLongError(LicodexError):
    """Raised when an assistant / RAG generated response exceeds storage limits.

    Historically the ``message.response`` column was ``VARCHAR(255)``. We now
    migrate it to ``TEXT`` (effectively unbounded for practical LLM replies),
    but this error is kept for two reasons:
      1. Defensive handling if a future storage policy re‑introduces a cap.
      2. Graceful degradation if the migration has not yet been applied and a
         long reply triggers a DB truncation error.
    """
    def __init__(self, length: int | None = None, limit: int | None = None):
        detail = "Assistant response exceeded storage capacity"
        parts: list[str] = []
        if length is not None:
            parts.append(f"length={length}")
        if limit is not None:
            parts.append(f"limit={limit}")
        if parts:
            detail += f" (" + ", ".join(parts) + ")"
        super().__init__(detail)


__all__ = [
    "LicodexError",
    "ResponseTooLongError",
]
