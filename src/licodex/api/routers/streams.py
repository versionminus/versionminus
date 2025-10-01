from fastapi import APIRouter

router = APIRouter(prefix="/streams", tags=["streams"])

@router.get("/sse", summary="SSE placeholder endpoint")
async def sse_placeholder():
    # A real implementation would return an EventSourceResponse streaming tokens.
    return {"detail": "SSE streaming not yet implemented"}
