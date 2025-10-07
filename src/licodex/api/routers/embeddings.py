"""
Note text ->
(embedding function) ->
1536-float vector ->
stored alongside note_id & metadata in Milvus ->
index makes nearest-neighbor search fast ->
search returns candidates ->
get original note content from pg
"""
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
import hashlib
from datetime import datetime
import json
from pymilvus import Collection, utility
from sqlalchemy.ext.asyncio import AsyncSession

from licodex.core.config import get_settings
from licodex.core.milvus.milvus import get_milvus
from licodex.core.modelhub import get_modelhub_client
from licodex.schemas.embeddings import EmbeddingRequest, SearchRequest, HealthResponse
from licodex.api import deps
from licodex.models.note import Note, NoteStatus
from sqlalchemy import select
from uuid import UUID

MAX_CHUNK_TOKENS = 800  # simple heuristic for splitting very long notes
CHUNK_OVERLAP = 50
MAX_VECTORS_PER_COLLECTION = 1000  # safety cap to avoid huge payloads

router = APIRouter(prefix="/embeddings", tags=["embeddings"])


def _split_text(text: str) -> List[str]:
    # Extremely naive tokenizer by whitespace. Improve later with tiktoken.
    words = text.split()
    if len(words) <= MAX_CHUNK_TOKENS:
        return [text]
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + MAX_CHUNK_TOKENS, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end == len(words):
            break
        start = max(end - CHUNK_OVERLAP, end)  # avoid negative; minimal overlap currently
    return chunks


def _embed_texts(texts: List[str], model: str, dim: int) -> List[List[float]]:
    client = get_modelhub_client()
    if client is None:
        raise HTTPException(status_code=503, detail="Embedding model client not configured")
    # OpenAI compatible embeddings API
    try:
        resp = client.embeddings.create(model=model, input=texts)  # type: ignore[attr-defined]
        vectors = [item.embedding for item in resp.data]
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {e}")
    # Optional dim validation
    for v in vectors:
        if len(v) != dim:
            raise HTTPException(status_code=500, detail=f"Embedding dimension mismatch {len(v)} != expected {dim}")
    return vectors


@router.get("/health", response_model=HealthResponse, summary="Milvus embeddings health")
async def embeddings_health():
    try:
        get_milvus()
        cols = utility.list_collections()
        return HealthResponse(collections=cols, ready=True, default_collection_present="notes" in cols)
    except Exception:  # pragma: no cover
        return HealthResponse(collections=[], ready=False, default_collection_present=False)


@router.post("/", summary="Create (and optionally store) embeddings")
async def create_embeddings(req: EmbeddingRequest, session: AsyncSession = Depends(deps.get_db)):
    # Normalize input to list
    inputs = [req.input] if isinstance(req.input, str) else list(req.input)
    if not inputs:
        raise HTTPException(status_code=400, detail="No input provided")

    settings = get_settings()
    dim = settings.rag_embedding_model_output or settings.embedding_default_dim or 1536

    # Expand and chunk any long inputs
    expanded_inputs: List[str] = []
    input_note_ids: List[str] | None = None
    if isinstance(req.note_ids, list):
        input_note_ids = []
    for idx, text in enumerate(inputs):
        pieces = _split_text(text)
        if input_note_ids is not None:
            # replicate note id per chunk
            nid = req.note_ids[idx] if req.note_ids and idx < len(req.note_ids) else ""
            input_note_ids.extend([nid] * len(pieces))
        expanded_inputs.extend(pieces)

    if input_note_ids is not None:
        req.note_ids = input_note_ids

    # Generate vectors using real embedding model
    model_name = req.model or settings.rag_embedding_model
    vectors = _embed_texts(expanded_inputs, model_name, dim)

    if not req.upsert:
        return {"model": req.model, "data": vectors, "dimensions": dim}

    collection_name = req.collection or "notes"
    try:
        get_milvus()  # ensures connection
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=503, detail=f"Milvus connection failed: {e}")

    if not utility.has_collection(collection_name):
        raise HTTPException(status_code=404, detail=f"Collection '{collection_name}' not found")

    coll = Collection(collection_name)
    # Identify schema ordering (skip auto id field). Expect a vector field named 'vector'.
    vector_field = next((f.name for f in coll.schema.fields if f.dtype.name == 'FLOAT_VECTOR'), None)
    if not vector_field:
        raise HTTPException(status_code=500, detail="No FLOAT_VECTOR field in collection schema")

    # For the 'notes' collection we expect order: id(auto) vector note_id user_id status metadata
    payload = [vectors]
    remaining_fields = [f.name for f in coll.schema.fields if not f.is_primary and f.name != vector_field]

    # Validate optional metadata lengths if provided
    def _validate_parallel(name: str, data: Optional[List[str]]):
        if data is not None and len(data) != len(inputs):
            raise HTTPException(status_code=400, detail=f"Field '{name}' length {len(data)} != inputs length {len(inputs)}")

    _validate_parallel("note_ids", req.note_ids)
    _validate_parallel("user_ids", req.user_ids)
    _validate_parallel("statuses", req.statuses)
    _validate_parallel("metadatas", req.metadatas)

    # Build enriched metadata baseline if needed
    enriched_metadatas: List[str] | None = None
    if req.metadatas is None:
        enriched_metadatas = []
        for text in expanded_inputs:
            first_line = text.strip().splitlines()[0][:120] if text.strip() else ""
            meta_obj = {
                "pseudo_title": first_line,
                "content_length": len(text),
                "created_at": datetime.utcnow().isoformat(),
            }
            enriched_metadatas.append(json.dumps(meta_obj))
    for fname in remaining_fields:
        if fname == 'note_id':
            payload.append(req.note_ids or ["" for _ in expanded_inputs])
        elif fname == 'user_id':
            payload.append(req.user_ids or ["" for _ in expanded_inputs])
        elif fname == 'status':
            payload.append(req.statuses or ["EMBEDDED" for _ in expanded_inputs])
        elif fname == 'metadata':
            payload.append(req.metadatas or enriched_metadatas or ["{}" for _ in expanded_inputs])
        else:
            payload.append(["" for _ in expanded_inputs])

    try:
        coll.insert(payload)
        coll.load()
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Milvus insert failed: {e}")

    # Mark associated notes as embedded (if note_ids supplied)
    if req.note_ids:
        try:
            ids_set = {nid for nid in req.note_ids if nid}
            if ids_set:
                # load notes and update
                stmt = select(Note).where(Note.id.in_(list(ids_set)))  # type: ignore[arg-type]
                res = await session.execute(stmt)
                for note in res.scalars():
                    note.embedded = True
                    note.embedded_at = datetime.utcnow()
                await session.flush()
                await session.commit()
        except Exception:  # pragma: no cover - don't fail main response
            pass

    return {"model": model_name, "data": vectors, "dimensions": dim, "collection": collection_name, "count": len(vectors)}


@router.delete("/{note_id}", summary="Delete embeddings for a note (and reset status)", status_code=204)
async def delete_note_embeddings(note_id: UUID, session: AsyncSession = Depends(deps.get_db)):
    """Delete all embeddings in the default collection for the given note id.

    Side effects:
      - Removes vectors from Milvus (best-effort; ignores errors)
      - Resets the note's embedded flag & timestamp and (if previously ERROR) sets status back to AVAILABLE
    """
    # Load note first so we can update state even if Milvus deletion fails
    stmt = select(Note).where(Note.id == note_id)
    res = await session.execute(stmt)
    note = res.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    # Attempt Milvus deletion
    try:  # pragma: no cover - external system interaction
        get_milvus()
        if utility.has_collection("notes"):
            coll = Collection("notes")
            coll.delete(expr=f"note_id == '{note_id}'")
    except Exception:
        # We purposely swallow errors to keep API idempotent
        pass
    # Reset embedding metadata
    note.embedded = False
    note.embedded_at = None
    if note.status == NoteStatus.ERROR:
        note.status = NoteStatus.AVAILABLE
    await session.flush()
    await session.commit()
    return None


@router.post("/search", summary="Vector similarity search against a collection")
async def search_embeddings(req: SearchRequest):
    settings = get_settings()
    dim = settings.rag_embedding_model_output or settings.embedding_default_dim or 1536
    collection_name = req.collection or "notes"

    try:
        get_milvus()
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=503, detail=f"Milvus connection failed: {e}")

    if not utility.has_collection(collection_name):
        raise HTTPException(status_code=404, detail=f"Collection '{collection_name}' not found")

    coll = Collection(collection_name)
    vector_field = next((f.name for f in coll.schema.fields if f.dtype.name == 'FLOAT_VECTOR'), None)
    if not vector_field:
        raise HTTPException(status_code=500, detail="No FLOAT_VECTOR field in collection schema")

    # Prepare query vector
    if req.vector is not None:
        if len(req.vector) != dim:
            raise HTTPException(status_code=400, detail=f"Provided vector dim {len(req.vector)} != expected {dim}")
        qvec = req.vector
    else:
        # Real embedding generation for query
        qvec = _embed_texts([req.query], settings.rag_embedding_model or req.model, dim)[0]

    search_params = {"metric_type": req.metric_type, "params": {"nprobe": 10}}
    try:
        coll.load()
        results = coll.search(data=[qvec], anns_field=vector_field, param=search_params, limit=req.top_k, output_fields=[f.name for f in coll.schema.fields if f.name != vector_field])
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Milvus search failed: {e}")

    hits_out = []
    if results:
        for hit in results[0]:  # first (and only) query vector
            record = {"id": hit.id, "distance": hit.distance}
            if hasattr(hit, 'entity') and hit.entity is not None:
                for fname in hit.entity.keys():
                    record[fname] = hit.entity.get(fname)
            hits_out.append(record)
    return {"collection": collection_name, "top_k": req.top_k, "metric_type": req.metric_type, "query_hash": hashlib.sha256(req.query.encode()).hexdigest()[:16], "results": hits_out}


@router.get("/collections", summary="List Milvus collections and their indexes")
async def list_collections():
    """Return all Milvus collections with basic index metadata for each field.

    For every collection we attempt to enumerate its indexes. Each index entry includes:
      - field_name
      - index_name (if available)
      - index_type / metric_type (if available in params)
      - raw params (opaque, driver-specific)

    Any per-collection errors are captured and surfaced in an 'error' key for that collection,
    without failing the entire response.
    """
    try:
        get_milvus()
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=503, detail=f"Milvus connection failed: {e}")

    try:
        names = utility.list_collections()
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Failed to list collections: {e}")

    out = []
    for name in names:
        col_info = {"name": name, "indexes": []}
        try:
            coll = Collection(name)
            for idx in getattr(coll, "indexes", []) or []:
                # Defensive extraction of parameters; structure can vary by pymilvus version
                params = getattr(idx, "params", {})
                if isinstance(params, list):  # some versions return list of dicts
                    # Flatten list into a single dict (later keys override earlier ones)
                    flat = {}
                    for p in params:
                        if isinstance(p, dict):
                            flat.update(p)
                    params = flat
                index_entry = {
                    "field_name": getattr(idx, "field_name", None),
                    "index_name": getattr(idx, "index_name", None) or (params.get("index_name") if isinstance(params, dict) else None),
                    "index_type": params.get("index_type") if isinstance(params, dict) else None,
                    "metric_type": params.get("metric_type") if isinstance(params, dict) else None,
                    "params": params,
                }
                col_info["indexes"].append(index_entry)
        except Exception as e:  # pragma: no cover
            col_info["error"] = str(e)
        out.append(col_info)

    return {"collections": out, "count": len(out)}


@router.get("/vectors", summary="List vectors for all Milvus collections")
async def list_all_vectors():
    """Return vectors for every Milvus collection.

    WARNING: Potentially large response. To avoid exhausting memory / network we cap
    the number of vectors returned per collection at MAX_VECTORS_PER_COLLECTION.

    Response shape:
      {
        "collections": [
           {
             "name": str,
             "vector_field": str | None,
             "count": int,                # total entities in collection
             "returned": int,             # number of vectors actually included
             "truncated": bool,           # true if capped
             "vectors": [[float, ...], ...]
           }, ...
        ],
        "total_vectors_returned": int
      }
    """
    try:
        get_milvus()
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=503, detail=f"Milvus connection failed: {e}")

    try:
        names = utility.list_collections()
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Failed to list collections: {e}")

    collections_out = []
    total_vectors = 0
    for name in names:
        info = {"name": name, "vector_field": None, "count": 0, "returned": 0, "truncated": False, "vectors": []}  # type: ignore[var-annotated]
        try:
            coll = Collection(name)
            coll.load()
            # Identify vector field (first FLOAT_VECTOR)
            vector_field = next((f.name for f in coll.schema.fields if f.dtype.name == 'FLOAT_VECTOR'), None)
            info["vector_field"] = vector_field
            info["count"] = int(getattr(coll, 'num_entities', 0))
            if not vector_field or info["count"] == 0:
                collections_out.append(info)
                continue
            # Determine primary key field to craft a permissive query expression
            pk_field = next((f.name for f in coll.schema.fields if f.is_primary), None)
            expr = f"{pk_field} >= 0" if pk_field else ""
            limit = min(info["count"], MAX_VECTORS_PER_COLLECTION)
            if info["count"] > MAX_VECTORS_PER_COLLECTION:
                info["truncated"] = True
            try:
                # Query all (capped) entities for just the vector field
                results = coll.query(expr=expr, output_fields=[vector_field], limit=limit)
                vectors = [r.get(vector_field) for r in results if isinstance(r, dict) and vector_field in r]
                info["vectors"] = vectors
                info["returned"] = len(vectors)
                total_vectors += len(vectors)
            except Exception as qerr:  # pragma: no cover
                info["error"] = f"query failed: {qerr}"  # type: ignore[index]
        except Exception as e:  # pragma: no cover
            info["error"] = str(e)  # type: ignore[index]
        collections_out.append(info)

    return {"collections": collections_out, "total_vectors_returned": total_vectors, "max_per_collection": MAX_VECTORS_PER_COLLECTION}


@router.get("/status/{note_id}", summary="Get embedding status for a note")
async def embedding_status(note_id: UUID, session: AsyncSession = Depends(deps.get_db)):
    """Return the embedding status for a note.

    Semantics:
      - 200 OK  -> note exists AND note.embedded == True (embedded_at populated)
      - 202 Accepted -> note exists BUT embedding not yet finished (embedded == False)
      - 404 Not Found -> note does not exist

    The body shape is identical for 200 and 202 so callers can inspect fields if desired.
    """
    stmt = select(Note).where(Note.id == note_id)
    res = await session.execute(stmt)
    note = res.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    body = {
        "note_id": str(note.id),
        "embedded": bool(note.embedded),
        "embedded_at": note.embedded_at,
        "status": note.status.value if hasattr(note.status, "value") else str(note.status),
    }
    if note.embedded:
        return body  # 200
    # Pending
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content=body)
