"""ModelHub client helpers.

Centralizes construction of external model provider clients (currently
OpenAI-compatible). This isolates credential handling and allows future
extension (multiple providers, caching, retry wrappers, etc.).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

try:  # pragma: no cover - optional dependency / runtime guard
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover - import failure path
    OpenAI = None  # type: ignore

from .config import get_settings
from .errors import NoSuchModelError


class ModelHubUnavailable(RuntimeError):
    """Raised when a model hub client cannot be constructed due to config."""


@lru_cache
def get_modelhub_client() -> Any:
    """Return a cached OpenAI-compatible client if configuration present.

    Returns
    -------
    OpenAI | None
        An instantiated `OpenAI` client or None if requirements aren't met.
    """
    settings = get_settings()
    if not (OpenAI and settings.modelhub_api_key and settings.modelhub_base_url):
        return None
    return OpenAI(  # type: ignore[operator]
        api_key=settings.modelhub_api_key.get_secret_value(),  # type: ignore[arg-type]
        base_url=settings.modelhub_base_url,
    )


def ensure_openai_client() -> Any:
    """Strict getter that raises if the client is unavailable."""
    client = get_modelhub_client()
    if client is None:
        raise ModelHubUnavailable("OpenAI client is not configured (missing dependency or credentials).")
    return client


def resolve_chat_model(requested: str | None) -> tuple[str, str]:
    """Resolve an inbound requested chat model name against policy.

    Current policy: only the configured default (``settings.chat_completion_model``)
    is allowed. This function centralizes the logic so future expansion to an
    allowlist or dynamic mapping happens in one place.

    Parameters
    ----------
    requested:
        Optional model identifier provided by the caller.

    Returns
    -------
    (resolved_model, reason)
        ``resolved_model`` is the model actually to be used.
        ``reason`` is one of: "requested_allowed", "default_used", "not_allowed_defaulted".
    """
    settings = get_settings()
    default_model = settings.chat_completion_model
    if not requested:
        return default_model, "default_used"
    if requested == default_model:
        return requested, "requested_allowed"
    # Mismatch: explicitly raise to let API map to 404 with model detail
    raise NoSuchModelError(requested)

def resolve_embedding_model(requested: str | None) -> str:
    """Resolve embedding model; raise if not matching configured default.

    Current policy mirrors chat models: only the configured default is allowed.
    This ensures a clear error with the attempted model name for the SDK/React.
    """
    settings = get_settings()
    default_model = settings.rag_embedding_model
    if not requested or requested == default_model:
        return default_model
    raise NoSuchModelError(requested)
