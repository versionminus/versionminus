from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from licodex.core.config import get_settings
from licodex.core.logging import configure_logging
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

app.include_router(health.router, prefix=settings.api_prefix)
app.include_router(users.router, prefix=settings.api_prefix)
app.include_router(threads.router, prefix=settings.api_prefix)
app.include_router(messages.router, prefix=settings.api_prefix)
app.include_router(models.router, prefix=settings.api_prefix)
app.include_router(embeddings.router, prefix=settings.api_prefix)
app.include_router(chat.router, prefix=settings.api_prefix)
app.include_router(streams.router, prefix=settings.api_prefix)
app.include_router(debug.router, prefix=settings.api_prefix)
app.include_router(notes.router, prefix=settings.api_prefix)
app.include_router(sources.router, prefix=settings.api_prefix)

@app.get("/")
async def root():
    return {"service": settings.app_name, "status": "ok"}
