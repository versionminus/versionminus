import uuid
import pytest


@pytest.mark.asyncio
async def test_note_update_flow(client):
    # create user
    user_resp = await client.post(
        "/api/v1/users/",
        json={
            "email": f"note-user-{uuid.uuid4()}@example.com",
        },
    )
    assert user_resp.status_code == 201, user_resp.text
    user_id = user_resp.json()["id"]

    # create note
    note_resp = await client.post(
        "/api/v1/notes/",
        json={
            "user_id": user_id,
            "content": "original content",
        },
    )
    assert note_resp.status_code == 201, note_resp.text
    note = note_resp.json()
    note_id = note["id"]
    assert note["content"] == "original content"

    # patch note content
    patch_resp = await client.patch(
        f"/api/v1/notes/{note_id}",
        json={"content": "updated content"},
    )
    assert patch_resp.status_code == 200, patch_resp.text
    updated = patch_resp.json()
    assert updated["id"] == note_id
    assert updated["content"] == "updated content"


@pytest.mark.asyncio
async def test_note_update_not_found(client):
    # attempt to patch a random UUID
    random_id = uuid.uuid4()
    resp = await client.patch(
        f"/api/v1/notes/{random_id}", json={"content": "won't work"}
    )
    assert resp.status_code == 404
    body = resp.json()
    assert body["detail"] == "Note not found"
