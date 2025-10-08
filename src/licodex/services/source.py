"""Service layer for retrieval sources."""
import uuid
from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from licodex.repositories import source as source_repo
from licodex.repositories import note as note_repo

__all__ = [
    "create_sources_for_group",
    "retrieve_relevant_notes",
    "list_sources",
]

async def create_sources_for_group(session: AsyncSession, *, sources_id: uuid.UUID, items: list[tuple]):
    """Persist a batch of Source rows.

    ``items`` is a list of tuples shaped either as ``(note_id, quote)`` or
    ``(note_id, quote, distance)`` (the latter preferred). Distance is optional
    to remain backward compatible with legacy callers or heuristic retrieval
    paths without a numeric score.
    """
    return await source_repo.create_many(session, sources_id=sources_id, rows=items)

async def list_sources(session: AsyncSession, sources_id: uuid.UUID):
    return await source_repo.list_by_group_id(session, sources_id)

async def retrieve_relevant_notes(session: AsyncSession, *, user_query: str, limit: int = 3) -> list[tuple[uuid.UUID, str, float | None]]:
    """Retrieve relevant notes for a user query.

    Preferred path:
        1. Use Milvus vector similarity over the ``notes`` collection.
        2. Generate an embedding for the query via model hub client.
        3. Map top-k (deduplicated) hits back to Note rows and extract snippets.

    Fallback path (any failure: missing Milvus, model client, errors):
        - Perform the legacy substring heuristic over all notes.

    Returns list[(note_id, quote_snippet)].
    """

    async def _fallback_substring() -> list[tuple[uuid.UUID, str, float | None]]:
        from sqlalchemy import select
        from licodex.models.note import Note
        res = await session.execute(select(Note))
        candidates = list(res.scalars().all())
        user_lower = user_query.lower()
        scored: list[tuple[float, tuple[uuid.UUID, str, float | None]]] = []
        for n in candidates:
            content_lower = n.content.lower()
            if user_lower in content_lower:
                idx = content_lower.index(user_lower)
                score = 1.0 / (1 + idx)
                snippet = n.content[max(0, idx-40): idx+len(user_query)+80]
                scored.append((score, (n.id, snippet.strip(), None)))
        scored.sort(key=lambda x: x[0], reverse=True)
        top = [pair for _score, pair in scored[:limit]]
        if len(top) < limit:
            for n in candidates:
                if n.id not in {nid for nid, _ in top}:
                    top.append((n.id, n.content[:120], None))
                if len(top) >= limit:
                    break
        return top[:limit]

    # Attempt semantic retrieval
    try:  # pragma: no cover - relies on external Milvus + model service
        from licodex.core.config import get_settings
        from licodex.core.modelhub import get_modelhub_client
        from licodex.core.milvus.milvus import get_milvus
        from pymilvus import Collection, utility

        settings = get_settings()
        # Ensure Milvus connection
        get_milvus()
        collection_name = "notes"
        if not utility.has_collection(collection_name):
            raise RuntimeError("notes collection missing")

        client = get_modelhub_client()
        if client is None:
            raise RuntimeError("embedding client unavailable")

        dim = settings.rag_embedding_model_output or settings.embedding_default_dim or 1536
        model_name = settings.rag_embedding_model
        # Generate embedding for query
        q_resp = client.embeddings.create(model=model_name, input=[user_query])  # type: ignore[attr-defined]
        qvec: List[float] = q_resp.data[0].embedding  # type: ignore[index]
        if len(qvec) != dim:
            # Dimension mismatch -> treat as failure to simplify
            raise RuntimeError(f"query embedding dim {len(qvec)} != expected {dim}")

        coll = Collection(collection_name)
        vector_field = next((f.name for f in coll.schema.fields if f.dtype.name == 'FLOAT_VECTOR'), None)
        if not vector_field:
            raise RuntimeError("no FLOAT_VECTOR field")
        # Build output fields except vector
        output_fields = [f.name for f in coll.schema.fields if f.name != vector_field]
        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
        coll.load()
        raw_results = coll.search(
            data=[qvec],
            anns_field=vector_field,
            param=search_params,
            limit=limit * 4,  # fetch some extra to deduplicate note_ids from chunked notes
            output_fields=output_fields,
        )
        if not raw_results:
            return await _fallback_substring()
        hits = raw_results[0]
        # Aggregate by note_id keeping best (lowest distance) hit
        best_by_note: dict[uuid.UUID, Tuple[float, dict]] = {}
        for h in hits:
            ent = getattr(h, "entity", None)
            if not ent:
                continue
            nid_raw = ent.get("note_id") if hasattr(ent, 'get') else None
            if not nid_raw:
                continue
            try:
                nid = uuid.UUID(str(nid_raw))
            except Exception:
                continue
            dist = getattr(h, "distance", None)
            if dist is None:
                continue
            prev = best_by_note.get(nid)
            if prev is None or dist < prev[0]:
                # Convert entity keys/values to plain dict for later use
                best_by_note[nid] = (dist, {k: ent.get(k) for k in ent.keys()})  # type: ignore[attr-defined]
        # Order by ascending distance
        ordered = sorted(best_by_note.items(), key=lambda kv: kv[1][0])[:limit]
        results: list[tuple[uuid.UUID, str, float | None]] = []
        for nid, (_dist, _edata) in ordered:
            note = await note_repo.get_by_id(session, nid)
            if not note or not getattr(note, "content", None):
                continue
            snippet = note.content[:240].strip()
            # Ensure non-empty snippet
            results.append((nid, snippet if snippet else "(empty note)", _dist))
            if len(results) >= limit:
                break
        if results:
            return results
        # If semantic path produced nothing, fallback
        return await _fallback_substring()
    except Exception:
        # Any failure triggers fallback heuristic
        return await _fallback_substring()
