# app/database.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# залишаємо SQLite, але з async драйвером
DATABASE_URL = "sqlite+aiosqlite:///./app.db"

engine = create_async_engine(
    DATABASE_URL,
    future=True,
    echo=False,
)

class Base(DeclarativeBase):
    pass

# фабрика асинхронних сесій
async_session_maker = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# dependency для FastAPI
async def get_db():
    async with async_session_maker() as session:
        yield session
