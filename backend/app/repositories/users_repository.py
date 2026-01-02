from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.user import User
import uuid

async def create_user(session: AsyncSession, name: str, email: str, hashed_password: str) -> User:
    user = User(
        id=str(uuid.uuid4()),
        name=name,
        email=email,
        hashed_password=hashed_password
    )
    session.add(user)
    return user

async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

async def get_user_by_id(session: AsyncSession, user_id: str) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
