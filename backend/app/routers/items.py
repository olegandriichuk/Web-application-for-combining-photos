# app/routers/items.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from .. import schemas, crud

router = APIRouter(prefix="/items", tags=["items"])

@router.get("", response_model=list[schemas.ItemRead])
async def list_items(db: AsyncSession = Depends(get_db)):
    return await crud.list_items(db)

@router.post("", response_model=schemas.ItemRead)
async def create_item(payload: schemas.ItemCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_item(db, payload)

# приклад збереження старих маршрутів, якщо були:
@router.get("/{item_id}", response_model=schemas.ItemRead)
async def get_item(item_id: int, db: AsyncSession = Depends(get_db)):
    obj = await crud.get_item(db, item_id)
    if not obj:
        raise HTTPException(404, "Item not found")
    return obj

@router.patch("/{item_id}", response_model=schemas.ItemRead)
async def update_item(item_id: int, payload: schemas.ItemUpdate, db: AsyncSession = Depends(get_db)):
    obj = await crud.update_item(db, item_id, payload)
    if not obj:
        raise HTTPException(404, "Item not found")
    return obj
