import os
import uuid
import asyncio
from typing import List
from io import BytesIO

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..repositories import photos_repository as repo
from ..services.s3_service import s3_service
from ..dependencies.auth import get_current_user
from ..models.user import User

router = APIRouter()

def _safe_ext(name: str | None) -> str:
    if not name:
        return ""
    _, ext = os.path.splitext(name)
    return ext if 0 < len(ext) <= 10 else ""

@router.post("", summary="Upload photos")
async def upload_photos(
    files: List[UploadFile] = File(...),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    async def process_single_file(f: UploadFile):
        """Process a single file upload"""
        fid = str(uuid.uuid4())
        ext = _safe_ext(f.filename)
        s3_key = f"photos/{fid}{ext}"

        # Read file content
        file_content = await f.read()
        file_size = len(file_content)

        # Upload to S3
        try:
            await s3_service.upload_file(
                file_data=file_content,
                s3_key=s3_key,
                content_type=f.content_type or "application/octet-stream",
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to upload file to S3: {str(e)}"
            )

        # Save metadata to database
        await repo.create_photo_meta(
            session,
            id=fid,
            s3_key=s3_key,
            original_name=f.filename or f"{fid}{ext}",
            mime=f.content_type or "application/octet-stream",
            size=file_size,
            user_id=current_user.id,
        )

        return fid

    # Process all files in parallel
    ids = await asyncio.gather(*[process_single_file(f) for f in files])

    await session.commit()
    return {"items": list(ids)}

@router.get("", summary="List photos")
async def list_photos(
    limit: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = await repo.list_photos(session, user_id=current_user.id, limit=limit, offset=offset)
    items = [
        {
            "id": r.id,
            "original_name": r.original_name,
            "mime": r.mime,
            "size": r.size,
            "created_at": r.created_at.isoformat()
            if hasattr(r.created_at, "isoformat")
            else str(r.created_at),
        }
        for r in rows
    ]
    return {"items": items}

@router.get("/{photo_id}", summary="View / download photo")
async def get_photo(
    photo_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    row = await repo.get_photo(session, photo_id)
    if not row:
        raise HTTPException(status_code=404, detail="Photo not found")

    if row.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Download from S3
    try:
        file_data = await s3_service.download_file(row.s3_key)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to download file from S3: {str(e)}"
        )

    # Return as streaming response
    return StreamingResponse(
        BytesIO(file_data),
        media_type=row.mime,
        headers={"Content-Disposition": f'inline; filename="{row.original_name}"'},
    )

@router.delete("/{photo_id}", summary="Delete photo")
async def delete_photo(
    photo_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    row = await repo.get_photo(session, photo_id)
    if not row:
        raise HTTPException(status_code=404, detail="Photo not found")

    if row.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Delete from S3
    try:
        await s3_service.delete_file(row.s3_key)
    except Exception:
        # Continue even if S3 deletion fails
        pass

    # Delete from database
    await repo.delete_photo(session, row)
    await session.commit()
    return {"ok": True, "id": photo_id}
