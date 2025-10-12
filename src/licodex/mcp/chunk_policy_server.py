"""Standalone MCP server exposing chunk-policy detection tools."""

from __future__ import annotations

from typing import Any, Dict, Optional

from licodex.core.chunking import ChunkBoundaryPolicy


def _heuristic(note: str) -> Dict[str, Any]:
    if "```" in note or "~~~" in note:
        policy = ChunkBoundaryPolicy.CODE_BLOCKS
        reason = "Contains fenced code blocks"
    elif any(line.strip().startswith(('#', '##', '###')) for line in note.splitlines() if line.strip()):
        policy = ChunkBoundaryPolicy.HEADINGS_LISTS
        reason = "Contains markdown headings"
    elif any(line.strip().startswith(('-', '*', '+', '1.', '2.', '3.')) for line in note.splitlines() if line.strip()):
        policy = ChunkBoundaryPolicy.HEADINGS_LISTS
        reason = "Contains list structure"
    elif len(note.split()) < 120:
        policy = ChunkBoundaryPolicy.MINIMAL_WORDS
        reason = "Short text"
    else:
        policy = ChunkBoundaryPolicy.PARAGRAPH_SENTENCE
        reason = "Default"
    return {"policy": policy.value, "reason": reason, "source": "mcp-tool"}


try:  # pragma: no cover - optional dependency path
    from fastapi import FastAPI
    from mcp.server.fastapi import MCPFastAPI

    app = FastAPI(title="Chunk Policy MCP")
    mcp = MCPFastAPI(app, "chunk-policy")  # type: ignore

    @mcp.tool("detect_chunk_boundary_policy")  # type: ignore[attr-defined]
    async def detect_chunk_boundary_policy(note: str, metadata: Optional[Dict[str, Any]] = None):
        return _heuristic(note)

except Exception:  # pragma: no cover - fallback simple server
    from fastapi import FastAPI

    app = FastAPI(title="Chunk Policy MCP (fallback)")

    @app.post("/tools/detect_chunk_boundary_policy")
    async def detect_chunk_boundary_policy(note: str, metadata: Optional[Dict[str, Any]] = None):
        return _heuristic(note)


def run(host: str = "0.0.0.0", port: int = 8080):  # pragma: no cover - manual invocation helper
    import uvicorn

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":  # pragma: no cover
    run()
