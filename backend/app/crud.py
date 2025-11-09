# app/crud.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from . import models, schemas

async def list_items(db: AsyncSession):
    res = await db.execute(
        select(models.Item).order_by(models.Item.id.desc())
    )
    return res.scalars().all()

async def create_item(db: AsyncSession, data: schemas.ItemCreate):
    obj = models.Item(**data.dict())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj

# якщо були update/delete — теж робимо async:
async def update_item(db: AsyncSession, item_id: int, data: schemas.ItemUpdate):
    res = await db.execute(select(models.Item).where(models.Item.id == item_id))
    obj = res.scalar_one_or_none()
    if not obj:
        return None
    for k, v in data.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return obj

async def get_item(db: AsyncSession, item_id: int):
    res = await db.execute(select(models.Item).where(models.Item.id == item_id))
    return res.scalar_one_or_none()
