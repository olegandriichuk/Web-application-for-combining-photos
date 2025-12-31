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
) -> Photo:
    obj = Photo(
        id=id,
        s3_key=s3_key,
        original_name=original_name,
        mime=mime,
        size=size,
    )
    session.add(obj)
    await session.flush()
    return obj

async def get_photo(session: AsyncSession, photo_id: str) -> Optional[Photo]:
    return await session.get(Photo, photo_id)

async def list_photos(
    session: AsyncSession,
    *,
    limit: int = 100,
    offset: int = 0,
) -> List[Photo]:
    stmt = (
        select(Photo)
        .order_by(Photo.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    res = await session.execute(stmt)
    return res.scalars().all()

async def delete_photo(session: AsyncSession, photo: Photo) -> None:
    await session.delete(photo)

