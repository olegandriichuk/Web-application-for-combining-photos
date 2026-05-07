# Author: Oleg Andriichuk, xandri07
# Bachelor's thesis - Web Application for Image Stitching, FIT VUT Brno, 2026

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

async def update_user(
    session: AsyncSession,
    user: User,
    *,
    name: str | None = None,
    email: str | None = None,
    hashed_password: str | None = None,
) -> User:
    if name is not None:
        user.name = name
    if email is not None:
        user.email = email
    if hashed_password is not None:
        user.hashed_password = hashed_password
    return user
