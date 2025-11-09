from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..repositories import items_repository as repo
from ..schemas.item import ItemRead, ItemCreate, ItemUpdate

router = APIRouter(prefix="/items", tags=["items"])

@router.get("", response_model=list[ItemRead])
async def list_items(session: AsyncSession = Depends(get_db)):
    return await repo.list_items(session)

@router.get("/{item_id}", response_model=ItemRead)
async def get_item(item_id: int, session: AsyncSession = Depends(get_db)):
    item = await repo.get_item(session, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.post("", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
async def create_item(payload: ItemCreate, session: AsyncSession = Depends(get_db)):
    item = await repo.create_item(session, payload)
    await session.commit()
    return item

@router.patch("/{item_id}", response_model=ItemRead)
async def update_item(item_id: int, payload: ItemUpdate, session: AsyncSession = Depends(get_db)):
    item = await repo.update_item(session, item_id, payload)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    await session.commit()
    return item

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: int, session: AsyncSession = Depends(get_db)):
    ok = await repo.delete_item(session, item_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Item not found")
    await session.commit()
    return
