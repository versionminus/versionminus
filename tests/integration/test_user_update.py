import uuid
import pytest

@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_user_email(client):
	r = await client.post('/api/v1/users/', json={"email": "old@example.com", "role": "user"})
	user_id = r.json()['id']
	patch = await client.patch(f'/api/v1/users/{user_id}/email', json={"email": "new@example.com"})
	assert patch.status_code == 200
	assert patch.json()['email'] == 'new@example.com'

@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_user_email_conflict(client):
	r1 = await client.post('/api/v1/users/', json={"email": "first@example.com", "role": "user"})
	r2 = await client.post('/api/v1/users/', json={"email": "second@example.com", "role": "user"})
	uid2 = r2.json()['id']
	conflict = await client.patch(f'/api/v1/users/{uid2}/email', json={"email": "first@example.com"})
	assert conflict.status_code == 409
