from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings

engine = create_async_engine(
  url=settings.DATABASE_URL, 
  echo = settings.DEBUG, 
  future = True, 
  pool_pre_ping = True, 
  pool_size = 20, 
  max_overflow = 10, 
  pool_recycle = 3600
)

localSession = async_sessionmaker(
    engine, 
    class_ = AsyncSession, 
    expire_on_commit=False,
    autocommit = False, 
    autoflush=False,
)

