"""OIDC / Auth0 bearer token verification utilities.

Provides a FastAPI dependency ``get_current_user`` that validates an incoming
Authorization: Bearer <token> header against the configured Auth0 tenant.

If authentication is disabled via settings.auth_enabled, the dependency returns
None (and downstream routes may choose to allow anonymous access) or raises if
strict enforcement is desired.

Implementation notes:
* JWKS are fetched from https://<domain>/.well-known/jwks.json and cached.
* We use python-jose for JWT verification.
* Only access tokens (opaque or JWT) signed with RS256 are expected (default).
* The ``sub`` claim is treated as the stable external user id; ``email`` is used
  to auto-provision a local user record if one does not exist yet.

Future improvements:
* Role/permission mapping from custom claims.
* Caching of user lookups to reduce DB traffic.
"""
from __future__ import annotations

import time
import uuid
import httpx
from functools import lru_cache
from typing import Any, Optional
from jose import jwt
from fastapi import Depends, HTTPException, status
from fastapi import Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from licodex.core.config import get_settings
from licodex.db.session import get_db
from licodex.models.user import User
from licodex.repositories.user import get_by_id as repo_get_by_id, create as repo_create

class JWKSCache:
    def __init__(self, ttl_seconds: int) -> None:
        self._ttl = ttl_seconds
        self._expires_at = 0.0
        self._jwks: dict[str, Any] | None = None

    async def get(self, domain: str) -> dict[str, Any]:
        now = time.time()
        if self._jwks and now < self._expires_at:
            return self._jwks
        url = f"https://{domain.rstrip('/')}/.well-known/jwks.json"
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                raise RuntimeError(f"Failed to fetch JWKS: {resp.status_code}")
            data = resp.json()
        self._jwks = data
        self._expires_at = now + self._ttl
        return data

@lru_cache
def _jwks_cache(ttl: int) -> JWKSCache:
    return JWKSCache(ttl)

async def _verify_token(token: str, settings) -> dict[str, Any]:
    if not settings.auth0_domain or not settings.auth0_api_audience:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Auth0 not configured")
    # Basic structural validation of JWT
    if token.count('.') != 2:
        raise HTTPException(status_code=401, detail="Malformed bearer token")
    # Normalize domain (may be full https URL in env)
    domain = settings.auth0_domain.strip()
    if domain.startswith("http://"):
        domain = domain[len("http://"):]
    elif domain.startswith("https://"):
        domain = domain[len("https://"):]
    domain = domain.rstrip('/')
    cache = _jwks_cache(settings.auth_jwks_cache_ttl_seconds)
    jwks = await cache.get(domain)
    # Build key set
    from jose import jwk
    from jose.utils import base64url_decode
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get("kid")
    if not kid:
        raise HTTPException(status_code=401, detail="Missing kid header")
    key = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
    if not key:
        raise HTTPException(status_code=401, detail="Unknown kid")
    public_key = jwk.construct(key)
    try:
        message, encoded_signature = token.rsplit('.', 1)
    except ValueError:
        raise HTTPException(status_code=401, detail="Malformed bearer token")
    decoded_signature = base64url_decode(encoded_signature.encode())
    if not public_key.verify(message.encode(), decoded_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    claims = jwt.decode(
        token,
        key,
        algorithms=settings.auth_algorithms,
        audience=settings.auth0_api_audience,
        issuer=settings.auth0_issuer,
    )
    return claims

async def get_current_user(
    authorization: Optional[str] = Header(None),
    session: AsyncSession = Depends(get_db),
    settings = Depends(get_settings),
    request: Request = None,  # FastAPI injects Request; default keeps signature simple
) -> Optional[User]:
    """Validate bearer token and return associated local User.

    If auth disabled, returns the first user (if any) or None.
    """
    if not settings.auth_enabled:
        # Anonymous mode: choose not to enforce; return None.
        return None
    # If middleware already validated the token it will have placed claims on request.state
    if request is not None and hasattr(request.state, "verified_claims"):
        claims = request.state.verified_claims  # type: ignore
    else:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing bearer token")
        token = authorization[len("Bearer "):].strip()
        try:
            claims = await _verify_token(token, settings)
        except HTTPException:
            raise
        except Exception as e:  # catch broader jose/httpx errors
            raise HTTPException(status_code=401, detail="Token verification failed") from e

    external_sub = claims.get("sub")
    email = claims.get("email")
    if not external_sub:
        raise HTTPException(status_code=401, detail="Missing sub claim")
    # Map external sub to a UUID (stable namespace). If sub is already a UUID, use it.
    try:
        user_id = uuid.UUID(external_sub)
    except Exception:
        # Derive a deterministic UUIDv5 from the Auth0 subject string.
        user_id = uuid.uuid5(uuid.NAMESPACE_URL, f"auth0:{external_sub}")

    user = await repo_get_by_id(session, user_id)
    if not user:
        if not email:
            raise HTTPException(status_code=404, detail="User not provisioned and email missing")
        # Auto-provision
        user = await repo_create(session, email=email, id=user_id)
        await session.commit()
    return user

__all__ = ["get_current_user"]
