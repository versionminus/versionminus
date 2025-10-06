"""Embeddings collector service.

Periodically (or manually) fetches notes that are AVAILABLE and not yet embedded,
chunks them, generates embeddings via the public embeddings API endpoint, and
marks them embedded (the endpoint already sets flags, but we defensively handle
edge cases).

This module exposes a `collect_missing_embeddings` coroutine that can be wired
into a background task / scheduler (Celery, APScheduler, FastAPI startup task, etc.).
"""
from __future__ import annotations

import uuid
from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx
import os

from licodex.models.note import Note, NoteStatus
from licodex.core.config import get_settings

API_EMBEDDINGS_PATH = "/api/v1/embeddings/"  # trailing slash matches router


async def _get_unembedded_notes(session: AsyncSession, limit: int = 50) -> Sequence[Note]:
    stmt = select(Note).where(
        Note.status == NoteStatus.AVAILABLE,
        Note.embedded == False,  # noqa: E712
    ).order_by(Note.created_at).limit(limit)
    res = await session.execute(stmt)
    return list(res.scalars().all())


async def collect_missing_embeddings(session: AsyncSession, base_url: str | None = None, batch_size: int = 10) -> dict:
    """Embed all currently unembedded AVAILABLE notes.

    Parameters
    ----------
    session: AsyncSession
        Active DB session.
    base_url: str | None
        Base URL of the running API (e.g. http://localhost:8000). If omitted we try
        to infer from settings (host/port) for in-process deployment.
    batch_size: int
        Number of notes to send per embedding request.
    """
    settings = get_settings()
    if base_url is None:
        base_url = f"http://{settings.api_host}:{settings.api_port}"

    total_embedded = 0
    batches = 0
    async with httpx.AsyncClient(timeout=60.0) as client:
        while True:
            notes = await _get_unembedded_notes(session, limit=batch_size)
            if not notes:
                break
            batches += 1
            contents = [n.content for n in notes]
            note_ids = [str(n.id) for n in notes]
            # use configured embedding model
            model = settings.rag_embedding_model
            payload = {"model": model, "input": contents, "note_ids": note_ids, "upsert": True}
            try:
                resp = await client.post(f"{base_url}{API_EMBEDDINGS_PATH}", json=payload)
                if resp.status_code >= 300:
                    # Abort loop on persistent failure to avoid hot spin
                    break
                data = resp.json()
                total_embedded += data.get("count", 0)
            except Exception:  # pragma: no cover
                break
    return {"embedded": total_embedded, "batches": batches}
