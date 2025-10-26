import pytest
from versionminus.schemas.user import UserCreate

@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_user(client):
	payload = {"email": "alice@example.com", "role": "user"}
	resp = await client.post('/api/v1/users/', json=payload)
	assert resp.status_code == 201
	body = resp.json()
	assert body['email'] == payload['email']

@pytest.mark.asyncio
@pytest.mark.integration
async def test_duplicate_email(client):
	payload = {"email": "bob@example.com", "role": "user"}
	resp1 = await client.post('/api/v1/users/', json=payload)
	assert resp1.status_code == 201
	resp2 = await client.post('/api/v1/users/', json=payload)
	assert resp2.status_code == 409
