"""Chat related Pydantic schemas.

Separated from the API router so they can be reused (e.g. in tests or
other services) and to keep routers focused on request handling logic.
"""

from typing import Literal
from pydantic import BaseModel, field_validator
from licodex.core.config import get_settings
import uuid

class ChatThreadMessageRequest(BaseModel):
    """Incoming request for stateful thread-based chat (hybrid model resolution).

    Hybrid approach: caller may omit ``model``; we inject the configured default.
    If a model is supplied and is not the configured allowed default we raise
    validation error early (422) instead of silently falling back.
    """

    thread_id: uuid.UUID
    content: str
    model: str | None = None
    temperature: float = 0.7

    @field_validator("model", mode="after")
    @classmethod
    def _validate_or_default_model(cls, v: str | None):
        settings = get_settings()
        allowed = {settings.chat_completion_model}
        if v is None:
            return settings.chat_completion_model
        if v not in allowed:
            raise ValueError(f"model '{v}' not allowed. Allowed: {sorted(allowed)}")
        return v


class ChatThreadMessageResponse(BaseModel):
    thread_id: uuid.UUID
    message_id: uuid.UUID
    content: str
    response: str
    model: str | None
    usage: dict
    source_id: uuid.UUID | None = None  # retrieval group id
    # list of {note_id, quote, distance?}
    sources: list[dict] | None = None


class ChatMessage(BaseModel):
    """Single chat message segment.

    Roles intentionally constrained to a small set for now. Future expansion
    (e.g. tool / function / system variations) can be added here without
    touching router logic.
    """

    role: Literal["user", "system", "assistant"]
    content: str


class ChatCompletionRequest(BaseModel):
    """Schema for stateless chat completion requests (hybrid model policy).

    ``model`` is optional for clients; if omitted we default to the configured
    chat completion model. Supplying a different model produces a 422 error.
    This enforces policy at the schema boundary while still allowing future
    runtime resolution extensions (e.g., multi-tenant override) without
    changing the public contract.
    """

    model: str | None = None
    messages: list[ChatMessage]
    temperature: float = 0.7

    @field_validator("model", mode="after")
    @classmethod
    def _validate_or_default_model(cls, v: str | None):
        settings = get_settings()
        allowed = {settings.chat_completion_model}
        if v is None:
            return settings.chat_completion_model
        if v not in allowed:
            raise ValueError(f"model '{v}' not allowed. Allowed: {sorted(allowed)}")
        return v
