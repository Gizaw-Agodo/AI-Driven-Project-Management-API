from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import localSession
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with localSession() as session:
        try:
            yield session
        finally:
            await session.close()
    