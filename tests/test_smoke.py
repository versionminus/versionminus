import pytest


@pytest.mark.asyncio
@pytest.mark.smoke
async def test_smoke_user_thread(client):
    # Root
    r_root = await client.get('/')
    assert r_root.status_code == 200
    # Create user
    payload = {"email": "smoke@example.com", "role": "user"}
    r_user = await client.post('/api/v1/users/', json=payload)
    assert r_user.status_code == 201
    user_id = r_user.json()['id']
    # Create thread
    r_thread = await client.post('/api/v1/threads/', json={"title": "smoke-thread", "user_id": user_id})
    assert r_thread.status_code == 201
    # List threads
    r_threads = await client.get('/api/v1/threads/')
    assert r_threads.status_code == 200
    assert any(t['id'] == r_thread.json()['id'] for t in r_threads.json())