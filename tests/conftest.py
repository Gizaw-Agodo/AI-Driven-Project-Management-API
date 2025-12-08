"""
Shared test fixtures.

🎓 ADVANCED CONCEPT: Conftest.py

What is conftest.py?
- Pytest automatically loads it
- Fixtures here are available in all tests
- Can have multiple (one per directory)
- No import needed!

Fixture Scopes:
- function: New for each test (default)
- class: New for each test class
- module: New for each module
- session: One for entire test run

Benefits:
- DRY (Don't Repeat Yourself)
- Consistent test setup
- Easy to modify globally
- Clear organization
"""

from sqlalchemy.ext.asyncio.session import AsyncSession


import asyncio
from typing import AsyncGenerator, Generator
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.db.base import Base
from app.api.deps import get_db
from app.core.config import settings
from app.models.user import User
from app.core.security import hash_password, create_access_token

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo = False, 
    poolclass = NullPool
)

TestSessionLocal = async_sessionmaker[AsyncSession](
    test_engine, 
    class_ = AsyncSession, 
    expire_on_commit=False, 
    autocommit = False, 
    autoflush = False
)

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """
    Create event loop for async tests.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope = "session", autouse=True)
async def setup_database(): 
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield 

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get test database session.
    """
    async with TestSessionLocal() as session:
        # Start transaction
        async with session.begin():
            yield session
            # Rollback after test (automatic if exception)
            await session.rollback()

@pytest.fixture
async def db_session_with_commit() -> AsyncGenerator[AsyncSession, None]:
    """
    Database session that actually commits.
    
    🎓 USE CASE: When you need to test commit behavior
    or when using relationships that require committed data.
    """
    async with TestSessionLocal() as session:
        yield session
        # Clean up after test
        await session.rollback()

