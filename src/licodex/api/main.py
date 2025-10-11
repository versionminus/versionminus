from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from licodex.core.config import get_settings
from licodex.core.logging import configure_logging
from fastapi import Depends
from licodex.api import deps
from licodex.api.routers import (
    health,
    users,
    threads,
    messages,
    models,
    embeddings,
    chat,
    streams,
    debug,
    notes,
    sources,
)

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(title=settings.app_name)

if settings.enable_cors:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

secure_dependencies: list = []  # deprecated usage; middleware handles auth

# Middleware approach ensures even endpoints without dependency declaration are protected.
if settings.auth_enabled:
    EXEMPT_PATHS = {
        "/",  # root
        f"{settings.api_prefix}/health/liveness",
        f"{settings.api_prefix}/health/readiness",
    }

    @app.middleware("http")
    async def auth_middleware(request: Request, call_next):
        # Allow exempt paths
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)
        auth = request.headers.get("Authorization")
        if (not auth or not auth.startswith("Bearer ")) and settings.auth_testing_mode:
            # Inject dummy claims for tests
            request.state.verified_claims = {
                "sub": "test-user",
                "email": "test@example.com",
                "iss": settings.auth0_issuer or "https://testing/",
                "aud": settings.auth0_api_audience or "https://testing-api/",
            }
            return await call_next(request)
        if not auth or not auth.startswith("Bearer "):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
        token = auth[len("Bearer "):].strip()
        try:
            from licodex.core.auth import _verify_token  # local import to avoid circular
            claims = await _verify_token(token, settings)
            request.state.verified_claims = claims
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token")
        return await call_next(request)

def _include(router):
    app.include_router(router, prefix=settings.api_prefix)

_include(health.router)
_include(users.router)
_include(threads.router)
_include(messages.router)
_include(models.router)
_include(embeddings.router)
_include(chat.router)
_include(streams.router)
_include(debug.router)
_include(notes.router)
_include(sources.router)

@app.get("/")
async def root():
    return {"service": settings.app_name, "status": "ok"}
