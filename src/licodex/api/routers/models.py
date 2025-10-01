from fastapi import APIRouter

router = APIRouter(prefix="/models", tags=["models"])

# Placeholder in-memory model registry; replace with DB or config-backed list later.
_MODELS = [
    {"id": "gpt-like-small", "capabilities": ["chat"], "status": "online"},
    {"id": "gpt-like-medium", "capabilities": ["chat", "embeddings"], "status": "online"},
]


@router.get("/", summary="List available models")
async def list_models():
    return _MODELS


@router.get("/{model_id}", summary="Get model metadata")
async def get_model(model_id: str):
    for m in _MODELS:
        if m["id"] == model_id:
            return m
    return {"error": {"type": "not_found", "message": "Model not found"}}
