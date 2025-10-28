from fastapi import APIRouter
from licodex.core.config import get_settings
import re

router = APIRouter(prefix="/debug", tags=["debug"])


def _sanitize_url(url: str) -> str:
    """Mask password inside a Postgres URL (very loose heuristic)."""
    return re.sub(r":[^:@/]+@", ":***@", url)


@router.get("/config", summary="Inspect current configuration (sanitized)")
async def debug_config():
    """Return a sanitized snapshot of runtime configuration for debugging.

    Secrets (passwords/API keys) are never returned directly; instead we
    surface presence booleans and masked URLs.
    """
    s = get_settings()
    data = {
        "app": {
            "name": s.app_name,
            "environment": s.environment,
            "log_level": s.log_level,
            "api_prefix": s.api_prefix,
            "host": s.api_host,
            "port": s.api_port,
        },
        "database": {
            "user": s.effective_db_user,
            # never expose raw password
            "host": s.effective_db_host,
            "port": s.effective_db_port,
            "name": s.effective_db_name,
            "url_sync_masked": _sanitize_url(s.database_url_sync),
            "url_async_masked": _sanitize_url(s.database_url_async),
        },
        "modelhub": {
            "provider": s.modelhub,
            "base_url": s.modelhub_base_url,
            "has_api_key": bool(s.modelhub_api_key),
            "default_chat_model": s.chat_completion_model,
        },
    }
    return data
