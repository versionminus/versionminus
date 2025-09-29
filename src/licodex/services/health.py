from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

async def check_db(session: AsyncSession) -> bool:
    """Simple DB connectivity check.
    Uses a lightweight SELECT 1 statement and returns True if the DB responds.
    """
    try:
        await session.execute(text("SELECT 1"))
        return True
    except Exception:  # pragma: no cover - defensive fallback
        return False
