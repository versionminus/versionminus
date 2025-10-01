from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/embeddings", tags=["embeddings"])


class EmbeddingRequest(BaseModel):
    model: str
    input: list[str] | str


@router.post("/", summary="Create embeddings")
async def create_embeddings(req: EmbeddingRequest):
    # Placeholder deterministic embedding (hash-based) for scaffolding.
    def embed(text: str) -> list[float]:
        h = abs(hash(text))
        return [(h % 1000) / 1000.0, ((h // 1000) % 1000) / 1000.0]

    if isinstance(req.input, str):
        vectors = [embed(req.input)]
    else:
        vectors = [embed(t) for t in req.input]
    return {"model": req.model, "data": vectors, "dimensions": len(vectors[0]) if vectors else 0}
