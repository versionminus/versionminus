import os
import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator

# Configure database for tests via settings module rather than hardcoding directly.
# Allow overriding with TEST_DATABASE_URL; fall back to a local sqlite file.
test_db_url = os.environ.get("TEST_DATABASE_URL", "sqlite+aiosqlite:///./tests/test.db")
os.environ.setdefault("DATABASE_URL", test_db_url)

from licodex.core import config as _config  # noqa: E402
_config.get_settings.cache_clear()  # ensure new env vars are picked up # type: ignore[attr-defined]
_settings = _config.get_settings()

from licodex.api.main import app  # noqa: E402
from licodex.db.session import AsyncSessionLocal, engine, Base  # noqa: E402
from licodex.models.user import User  # noqa: E402
from sqlalchemy import delete  # noqa: E402

@pytest_asyncio.fixture(autouse=True, scope="session")
async def prepare_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="session")
def settings():
    """Expose application settings to tests if needed."""
    return _settings

@pytest_asyncio.fixture()
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:  # type: ignore
        yield session

@pytest_asyncio.fixture()
async def client():
    # httpx >=0.28 removed the 'app=' shortcut; use ASGITransport explicitly
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

@pytest_asyncio.fixture(autouse=True)
async def _clear_user_table():
    """Ensure isolated tests by clearing user table before each test.
    Uses a separate session to avoid interfering with request-scoped sessions.
    """
    async with AsyncSessionLocal() as session:  # type: ignore
        await session.execute(delete(User))
        await session.commit()
    yield
