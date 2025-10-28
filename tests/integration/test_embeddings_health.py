import pytest

# Tests for /api/v1/embeddings/health endpoint

@pytest.mark.asyncio
@pytest.mark.integration
async def test_embeddings_health_ready_with_default(client, monkeypatch):
    """Milvus reachable; 'notes' present => ready True and default_collection_present True."""
    from versionminus.api.routers import embeddings as emb
    monkeypatch.setattr(emb, "get_milvus", lambda: None)
    monkeypatch.setattr(emb.utility, "list_collections", lambda: ["notes", "other"])

    resp = await client.get("/api/v1/embeddings/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ready"] is True
    assert data["default_collection_present"] is True
    assert "notes" in data["collections"]

@pytest.mark.asyncio
@pytest.mark.integration
async def test_embeddings_health_ready_without_default(client, monkeypatch):
    """Milvus reachable; 'notes' absent => ready True but default_collection_present False."""
    from versionminus.api.routers import embeddings as emb
    monkeypatch.setattr(emb, "get_milvus", lambda: None)
    monkeypatch.setattr(emb.utility, "list_collections", lambda: ["foo", "bar"])

    resp = await client.get("/api/v1/embeddings/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ready"] is True
    assert data["default_collection_present"] is False
    assert data["collections"] == ["foo", "bar"]

@pytest.mark.asyncio
@pytest.mark.integration
async def test_embeddings_health_not_ready(client, monkeypatch):
    """Milvus not reachable => ready False and empty collections."""
    from versionminus.api.routers import embeddings as emb
    def _raise():  # simulate connection failure
        raise RuntimeError("milvus down")
    monkeypatch.setattr(emb, "get_milvus", _raise)

    resp = await client.get("/api/v1/embeddings/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ready"] is False
    assert data["default_collection_present"] is False
    assert data["collections"] == []
