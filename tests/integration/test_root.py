import pytest

@pytest.mark.asyncio
@pytest.mark.integration
async def test_root(client):
	resp = await client.get('/')
	assert resp.status_code == 200
	data = resp.json()
	assert data['status'] == 'ok'
	assert 'service' in data
