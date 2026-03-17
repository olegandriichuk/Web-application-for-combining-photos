# app/database.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import NullPool
from .config import settings


DATABASE_URL = settings.database_url

# NullPool ensures a fresh connection per request for SQLite,
# preventing stale column reads after schema changes.
engine = create_async_engine(
    DATABASE_URL,
    future=True,
    echo=False,
    poolclass=NullPool,
)

class Base(DeclarativeBase):
    pass


async_session_maker = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# dependency for FastAPI
async def get_db():
    async with async_session_maker() as session:
        yield session
