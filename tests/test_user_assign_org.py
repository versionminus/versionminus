import pytest

@pytest.mark.asyncio
async def test_assign_user_to_org(client):
    # create organisation
    org_resp = await client.post('/api/v1/organisations/', json={"name": "Acme"})
    assert org_resp.status_code == 201
    org_id = org_resp.json()['id']

    # create user
    user_resp = await client.post('/api/v1/users/', json={"email": "assign@example.com", "role": "user"})
    assert user_resp.status_code == 201
    user_id = user_resp.json()['id']

    # assign
    patch = await client.patch(f'/api/v1/users/{user_id}/organisation/{org_id}')
    assert patch.status_code == 200, patch.text
    body = patch.json()
    assert body['organisation'] is not None
    assert body['organisation']['id'] == org_id
    assert body['organisation']['name'] == 'Acme'

