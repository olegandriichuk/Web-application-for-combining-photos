from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.item import Item
from ..schemas.item import ItemCreate, ItemUpdate

async def list_items(session: AsyncSession) -> List[Item]:
    stmt = select(Item).order_by(Item.id.desc())
    res = await session.execute(stmt)
    return res.scalars().all()

async def get_item(session: AsyncSession, item_id: int) -> Optional[Item]:
    return await session.get(Item, item_id)

async def create_item(session: AsyncSession, payload: ItemCreate) -> Item:
    obj = Item(**payload.model_dump())
    session.add(obj)
    await session.flush()  # щоб мати obj.id без коміту
    return obj

async def update_item(session: AsyncSession, item_id: int, payload: ItemUpdate) -> Optional[Item]:
    obj = await session.get(Item, item_id)
    if not obj:
        return None
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(obj, k, v)
    await session.flush()
    return obj

async def delete_item(session: AsyncSession, item_id: int) -> bool:
    obj = await session.get(Item, item_id)
    if not obj:
        return False
    await session.delete(obj)
    return True
