import uuid
import pytest

@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_users_empty(client):
	resp = await client.get('/api/v1/users/')
	assert resp.status_code == 200
	assert resp.json() == []

@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_users_after_create(client):
	emails = ["a@example.com", "b@example.com", "c@example.com"]
	for e in emails:
		r = await client.post('/api/v1/users/', json={"email": e, "role": "user"})
		assert r.status_code == 201
	resp = await client.get('/api/v1/users/')
	body = resp.json()
	assert [u['email'] for u in body] == emails
