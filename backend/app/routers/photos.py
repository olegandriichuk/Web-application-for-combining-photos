import os
import uuid
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
import aiofiles

from ..database import get_db
from ..repositories import photos_repository as repo

router = APIRouter()

STORAGE_DIR = os.path.join(os.getcwd(), "data", "photos")
os.makedirs(STORAGE_DIR, exist_ok=True)

def _safe_ext(name: str | None) -> str:
    if not name:
        return ""
    _, ext = os.path.splitext(name)
    return ext if 0 < len(ext) <= 10 else ""

@router.post("", summary="Завантажити фото")
async def upload_photos(
    files: List[UploadFile] = File(...),
    session: AsyncSession = Depends(get_db),
):
    if not files:
        raise HTTPException(status_code=400, detail="Немає файлів")

    ids: List[str] = []
    for f in files:
        fid = str(uuid.uuid4())
        ext = _safe_ext(f.filename)
        stored_name = f"{fid}{ext}"
        stored_path = os.path.join(STORAGE_DIR, stored_name)

        # асинхронний запис файлу
        async with aiofiles.open(stored_path, "wb") as out:
            while True:
                chunk = await f.read(1024 * 1024)
                if not chunk:
                    break
                await out.write(chunk)

        size = os.path.getsize(stored_path)

        await repo.create_photo_meta(
            session,
            id=fid,
            stored_name=stored_name,
            original_name=f.filename or stored_name,
            mime=f.content_type or "application/octet-stream",
            size=size,
        )
        ids.append(fid)

    await session.commit()
    return {"items": ids}

@router.get("", summary="Список фото")
async def list_photos(
    limit: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(get_db),
):
    rows = await repo.list_photos(session, limit=limit, offset=offset)
    items = [
        {
            "id": r.id,
            "original_name": r.original_name,
            "mime": r.mime,
            "size": r.size,
            "created_at": r.created_at.isoformat() if hasattr(r.created_at, "isoformat") else str(r.created_at),
        }
        for r in rows
    ]
    return {"items": items}

@router.get("/{photo_id}", summary="Переглянути/скачати фото")
async def get_photo(photo_id: str, session: AsyncSession = Depends(get_db)):
    row = await repo.get_photo(session, photo_id)
    if not row:
        raise HTTPException(status_code=404, detail="Фото не знайдено")

    path = os.path.join(STORAGE_DIR, row.stored_name)
    if not os.path.exists(path):
        raise HTTPException(status_code=410, detail="Файл відсутній на диску")

    return FileResponse(path, media_type=row.mime, filename=row.original_name)

@router.delete("/{photo_id}", summary="Видалити фото")
async def delete_photo(photo_id: str, session: AsyncSession = Depends(get_db)):
    row = await repo.get_photo(session, photo_id)
    if not row:
        raise HTTPException(status_code=404, detail="Фото не знайдено")

    path = os.path.join(STORAGE_DIR, row.stored_name)
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass

    await repo.delete_photo(session, row)
    await session.commit()
    return {"ok": True, "id": photo_id}
