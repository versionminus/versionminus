from __future__ import annotations
from functools import lru_cache
from pymilvus import connections, utility
from licodex.core.config import get_settings
import time, os

class Milvus:
    """Encapsulates a resilient Milvus connection.

    Parameters
    ----------
    host: str | None
        Target Milvus host. If None, falls back to settings.milvus_host or 'localhost'.
    port: int | str | None
        Target Milvus port. If None, falls back to settings.milvus_http_port or 19530.

    Behavior
    --------
    On construction this attempts to (re)establish the global 'default' PyMilvus connection.
    A retry loop (configurable via env vars) validates readiness via a lightweight
    API call (utility.list_collections). Failure to connect within the timeout raises RuntimeError.

    Environment overrides:
      MILVUS_CONNECT_TIMEOUT  (seconds, default 60)
      MILVUS_CONNECT_INTERVAL (seconds, default 2.0)

    Notes
    -----
    Only a single global alias ('default') is used. The *first* successfully created
    Milvus instance effectively sets the connection target. Subsequent instances with
    different host/port values will reuse the existing connection (PyMilvus limitation
    around the implicit default alias). To deliberately reconnect to a different host
    you must call `connections.disconnect("default")` before constructing another instance.
    """

    def __init__(self, host: str | None = None, port: int | str | None = None):
        settings = get_settings()
        self.host = host or settings.milvus_host
        resolved_port: int | str = port or settings.milvus_http_port
        self.port = str(resolved_port)
        # Use central settings (which already honor env vars via pydantic Settings)
        timeout = float(settings.milvus_connect_timeout)
        interval = float(settings.milvus_connect_interval)

        deadline = time.time() + timeout
        last_err: Exception | None = None
        attempt = 0
        while time.time() < deadline:
            attempt += 1
            try:
                if not connections.has_connection("default"):
                    connections.connect("default", host=self.host, port=self.port)
                # readiness check (will raise if not ready)
                utility.list_collections()
                if attempt > 1:
                    print(f"[milvus-core] Connected to Milvus at {self.host}:{self.port} after {attempt} attempts")
                return
            except Exception as e:  # pragma: no cover
                last_err = e
                time.sleep(interval)
        # Exhausted retries
        msg = f"Failed to connect to Milvus at {self.host}:{self.port} within {timeout}s (last error: {last_err})"
        print(f"[milvus-core] ERROR {msg}")
        raise RuntimeError(msg) from last_err

    def list_collections(self):
        return utility.list_collections()

@lru_cache
def get_milvus(host: str | None = None, port: int | str | None = None) -> Milvus:  # pragma: no cover
    """Return (and cache) a Milvus instance keyed by host/port.

    The cache ensures we do not re-run the retry loop repeatedly in typical usage.

    Examples
    --------
    get_milvus()                       -> uses configured / default host
    get_milvus(host="localhost")       -> explicit localhost (e.g. inside Milvus container)
    get_milvus(host="licodex-milvus", port=19530) -> default
    """
    return Milvus(host=host, port=port)

__all__ = ["Milvus", "get_milvus"]
