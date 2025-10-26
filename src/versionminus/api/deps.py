"""Centralized FastAPI dependency definitions for the API layer.

Routers should import dependencies from here instead of directly from
their underlying implementation modules. This provides:

* A stable import surface (refactors in lower layers don't ripple up)
* Easier test overrides via ``app.dependency_overrides[deps.get_db]``
* A single location to add cross‑cutting concerns (tracing, metrics,
  logging wrappers, multi‑tenancy, etc.) around dependencies later.

Add new dependency callables here as the API grows.
"""

from versionminus.db.session import get_db
from versionminus.core.auth import get_current_user

__all__ = ["get_db", "get_current_user"]
