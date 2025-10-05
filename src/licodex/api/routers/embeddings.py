from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import hashlib
from pymilvus import Collection, utility
from licodex.core.config import get_settings
from licodex.core.milvus.milvus import get_milvus

router = APIRouter(prefix="/embeddings", tags=["embeddings"])


class EmbeddingRequest(BaseModel):
    model: str
    input: list[str] | str
    collection: Optional[str] = None  # default to 'notes' if not provided
    upsert: bool = True               # if false, only generate and return vectors
    # Optional metadata for insertion
    note_ids: Optional[List[str]] = Field(default=None, description="Parallel list of note ids (len must match inputs if provided)")
    user_ids: Optional[List[str]] = Field(default=None, description="Parallel list of user ids (len must match inputs if provided)")
    statuses: Optional[List[str]] = Field(default=None, description="Parallel list of statuses (len must match inputs if provided)")
    metadatas: Optional[List[str]] = Field(default=None, description="Parallel list of JSON metadata strings (len must match inputs if provided)")


class SearchRequest(BaseModel):
    collection: Optional[str] = None
    query: str
    top_k: int = 5
    metric_type: str = Field(default="L2", pattern="^(L2|IP|COSINE)$")
    # Optionally allow raw embedding vector for advanced clients
    vector: Optional[List[float]] = None


class HealthResponse(BaseModel):
    collections: List[str]
    ready: bool
    default_collection_present: bool


def _hash_embedding(text: str, dim: int) -> List[float]:
    # Stable pseudo-embedding using repeated SHA256 expansion to required dim
    needed = dim * 4
    buf = b""
    i = 0
    while len(buf) < needed:
        buf += hashlib.sha256(f"{i}:{text}".encode("utf-8")).digest()
        i += 1
    out: List[float] = []
    for off in range(0, needed, 4):
        out.append(int.from_bytes(buf[off:off+4], 'big') / 0xFFFFFFFF)
    return out[:dim]


@router.get("/health", response_model=HealthResponse, summary="Milvus embeddings health")
async def embeddings_health():
    try:
        get_milvus()
        cols = utility.list_collections()
        return HealthResponse(collections=cols, ready=True, default_collection_present="notes" in cols)
    except Exception:  # pragma: no cover
        return HealthResponse(collections=[], ready=False, default_collection_present=False)


@router.post("/", summary="Create (and optionally store) embeddings")
async def create_embeddings(req: EmbeddingRequest):
    # Normalize input to list
    inputs = [req.input] if isinstance(req.input, str) else list(req.input)
    if not inputs:
        raise HTTPException(status_code=400, detail="No input provided")

    settings = get_settings()
    dim = settings.rag_embedding_model_output or settings.embedding_default_dim or 1536

    # Generate vectors
    vectors = [_hash_embedding(text, dim) for text in inputs]

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

    for fname in remaining_fields:
        if fname == 'note_id':
            payload.append(req.note_ids or ["" for _ in inputs])
        elif fname == 'user_id':
            payload.append(req.user_ids or ["" for _ in inputs])
        elif fname == 'status':
            payload.append(req.statuses or ["EMBEDDED" for _ in inputs])
        elif fname == 'metadata':
            payload.append(req.metadatas or ["{}" for _ in inputs])
        else:
            payload.append(["" for _ in inputs])

    try:
        coll.insert(payload)
        coll.load()
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Milvus insert failed: {e}")

    return {"model": req.model, "data": vectors, "dimensions": dim, "collection": collection_name, "count": len(vectors)}


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
        qvec = _hash_embedding(req.query, dim)

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
