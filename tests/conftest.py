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


# ==================== CLIENT FIXTURES ====================
@pytest.fixture
async def client(db_session:AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db

    #create async client 
    async with AsyncClient(
        transport=ASGITransport(app = app),
        base_url="http://test"
    ) as ac:
        yield ac
    
    #remove ovveride
    app.dependency_overrides.clear()

@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    user = User(
        email = "testuser@example.com",
        username = "testuser",
        full_name = "Test User",
        hasshed_password = hash_password('TestPass123'),
        is_active = True,
        is_superuser = False
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user 

@pytest.fixture
async def test_superuser(db_session: AsyncSession) -> User:
    """Create a superuser for admin tests."""
    user = User(
        email="admin@example.com",
        username="admin",
        full_name="Admin User",
        hashed_password=hash_password("AdminPass123"),
        is_active=True,
        is_superuser=True,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user

@pytest.fixture
async def inactive_user(db_session: AsyncSession) -> User:
    """Create an inactive user for testing."""
    user = User(
        email="inactive@example.com",
        username="inactive",
        full_name="Inactive User",
        hashed_password=hash_password("TestPass123"),
        is_active=False,
        is_superuser=False,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture
def user_token(test_user: User) -> str:
    """
    Get access token for test user.
    """
    return create_access_token(
        data={
            "sub": str(test_user.id),
            "username": test_user.username,
            "email": test_user.email,
        }
    )

@pytest.fixture
def auth_headers(user_token: str) -> dict:
    """
    Auth headers for requests.
    """
    return {"Authorization": f"Bearer {user_token}"}
