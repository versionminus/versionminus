import uuid
import pytest

@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_user(client):
	r = await client.post('/api/v1/users/', json={"email": "del@example.com", "role": "user"})
	uid = r.json()['id']
	d = await client.delete(f'/api/v1/users/{uid}')
	assert d.status_code == 204
	# verify gone
	again = await client.delete(f'/api/v1/users/{uid}')
	assert again.status_code == 404

@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_user_not_found(client):
	random_id = str(uuid.uuid4())
	resp = await client.delete(f'/api/v1/users/{random_id}')
	assert resp.status_code == 404
