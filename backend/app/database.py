# app/database.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
# SQLite: NullPool was required to prevent stale column reads after schema changes on SQLite
# from sqlalchemy.pool import NullPool
from .config import settings


DATABASE_URL = settings.database_url

engine = create_async_engine(
    DATABASE_URL.split("?")[0],  # strip query params — ssl handled via connect_args
    future=True,
    echo=False,
    pool_pre_ping=True,   # reconnect if Neon closes idle connections
    pool_size=20,         # handle many concurrent tile requests
    max_overflow=20,
    connect_args={"ssl": True},  # required for Neon and other cloud PostgreSQL
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
