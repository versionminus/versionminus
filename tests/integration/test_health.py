import pytest

@pytest.mark.asyncio
@pytest.mark.integration
async def test_liveness(client):
	resp = await client.get('/api/v1/health/liveness')
	assert resp.status_code == 200
	assert resp.json()['status'] == 'ok'

@pytest.mark.asyncio
@pytest.mark.integration
async def test_readiness(client):
	resp = await client.get('/api/v1/health/readiness')
	assert resp.status_code == 200
	assert resp.json()['status'] == 'ready'
