from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.photo import Photo


async def create_photo_meta(
    session: AsyncSession,
    *,
    id: str,
    s3_key: str,
    original_name: str,
    mime: str,
    size: int,
    user_id: str,
    project_id: str,
) -> Photo:
    obj = Photo(
        id=id,
        s3_key=s3_key,
        original_name=original_name,
        mime=mime,
        size=size,
        user_id=user_id,
        project_id=project_id,
    )
    session.add(obj)
    await session.flush()
    return obj


async def get_photo(session: AsyncSession, photo_id: str) -> Optional[Photo]:
    return await session.get(Photo, photo_id)


async def get_photo_with_ownership_check(
    session: AsyncSession,
    photo_id: str,
    user_id: str,
    project_id: str,
) -> Optional[Photo]:
    """Get photo only if it belongs to user AND project"""
    stmt = select(Photo).where(
        Photo.id == photo_id,
        Photo.user_id == user_id,
        Photo.project_id == project_id,
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_photos(
    session: AsyncSession,
    *,
    user_id: str,
    project_id: str,
    limit: int = 100,
    offset: int = 0,
) -> List[Photo]:
    stmt = (
        select(Photo)
        .where(
            Photo.user_id == user_id,
            Photo.project_id == project_id
        )
        .order_by(Photo.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    res = await session.execute(stmt)
    return list(res.scalars().all())


async def delete_photo(session: AsyncSession, photo: Photo) -> None:
    await session.delete(photo)
