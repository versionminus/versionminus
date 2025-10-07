import uuid
import pytest

@pytest.mark.asyncio
async def test_user_create_with_forced_id(client):
    forced_id = uuid.uuid4()
    payload = {"id": str(forced_id), "email": "forced@example.com", "role": "user"}
    resp = await client.post("/api/v1/users/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["id"] == str(forced_id)
    # Re-post same email & id should now 409
    resp2 = await client.post("/api/v1/users/", json=payload)
    assert resp2.status_code == 409
