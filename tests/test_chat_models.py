import pytest
from versionminus.core.config import get_settings

# Using httpx AsyncClient fixture from conftest (client)

@pytest.mark.asyncio
async def test_chat_completion_default_model_injected(client):
    settings = get_settings()
    payload = {
        # omit model on purpose
        "messages": [{"role": "user", "content": "Hello"}],
        "temperature": 0.5,
    }
    r = await client.post(f"{settings.api_prefix}/chat/completions", json=payload)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["model"] == settings.chat_completion_model
    assert body.get("resolution", {}).get("reason") in {"default_used", "requested_allowed"}


@pytest.mark.asyncio
async def test_chat_completion_invalid_model_rejected(client):
    settings = get_settings()
    payload = {
        "model": settings.chat_completion_model + "_typo",
        "messages": [{"role": "user", "content": "Hi"}],
    }
    r = await client.post(f"{settings.api_prefix}/chat/completions", json=payload)
    # Pydantic validation error -> 422
    assert r.status_code == 422
    data = r.json()
    # Ensure error mentions model
    assert any("model" in (err.get("loc")[-1] if err.get("loc") else "") for err in data.get("detail", []))


@pytest.mark.asyncio
async def test_chat_thread_request_model_default(client, db_session):
    from versionminus.models.user import User
    from versionminus.models.thread import Thread
    from versionminus.db.session import AsyncSessionLocal

    # Create a user and thread via ORM directly
    async with AsyncSessionLocal() as session:  # type: ignore
        user = User(email="u@example.com", role="user")
        session.add(user)
        await session.flush()
        thread = Thread(title="t1", user_id=user.id)
        session.add(thread)
        await session.commit()
        tid = thread.id

    settings = get_settings()
    resp = await client.post(
        f"{settings.api_prefix}/chat/send",
        json={"thread_id": str(tid), "content": "Hello from thread"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["model"] == settings.chat_completion_model


@pytest.mark.asyncio
async def test_chat_thread_request_invalid_model_rejected(client, db_session):
    from versionminus.models.user import User
    from versionminus.models.thread import Thread
    from versionminus.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as session:  # type: ignore
        user = User(email="x@example.com", role="user")
        session.add(user)
        await session.flush()
        thread = Thread(title="t2", user_id=user.id)
        session.add(thread)
        await session.commit()
        tid = thread.id

    settings = get_settings()
    resp = await client.post(
        f"{settings.api_prefix}/chat/send",
        json={"thread_id": str(tid), "content": "Hi", "model": settings.chat_completion_model + "_bad"},
    )
    assert resp.status_code == 422
    data = resp.json()
    assert any("model" in (err.get("loc")[-1] if err.get("loc") else "") for err in data.get("detail", []))
