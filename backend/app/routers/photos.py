import asyncio
import io
import os
import uuid
from typing import Tuple

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Response
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..repositories import photos_repository as photo_repo
from ..services.s3_service import s3_service
from ..services.deletion_service import deletion_service
from ..dependencies.auth import get_current_user
from ..dependencies.roles import require_project_role
from ..models.user import User
from ..models.project import Project
from ..schemas.photo import PhotoOut

router = APIRouter()


def _safe_ext(name: str | None) -> str:
    if not name:
        return ""
    _, ext = os.path.splitext(name)
    return ext if 0 < len(ext) <= 10 else ""


def _generate_preview_bytes(file_content: bytes) -> bytes:
    """Resize image to max 800x800 JPEG at quality 75. Must run in a thread."""
    img = Image.open(io.BytesIO(file_content))
    img.thumbnail((800, 800), Image.LANCZOS)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    output = io.BytesIO()
    img.save(output, format="JPEG", quality=75)
    return output.getvalue()


@router.post("/projects/{project_id}/photos", summary="Upload single photo to project g")
async def upload_photo(
    project_id: str,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    project_role: Tuple[Project, str] = Depends(require_project_role("owner", "editor")),
):
    """
    Upload ONE photo to a specific project.
    Returns: {"item": "<photo_id>"}
    """
    # 2) Generate photo id and S3 key
    fid = str(uuid.uuid4())
    ext = _safe_ext(file.filename)
    s3_key = f"photos/{fid}{ext}"

    # 3) Read file content (note: loads entire file into RAM)
    file_content = await file.read()
    if not file_content:
        raise HTTPException(status_code=400, detail="Empty file")

    file_size = len(file_content)
    content_type = file.content_type or "application/octet-stream"
    original_name = file.filename or f"{fid}{ext}"

    # 4) Upload original to S3
    try:
        await s3_service.upload_file(
            file_data=file_content,
            s3_key=s3_key,
            content_type=content_type,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file to S3: {str(e)}")

    # 5) Read original image dimensions
    original_width: int | None = None
    original_height: int | None = None
    try:
        with Image.open(io.BytesIO(file_content)) as img:
            original_width, original_height = img.size
    except Exception:
        pass

    # 6) Generate preview and upload to S3
    preview_s3_key: str | None = None
    try:
        preview_bytes = await asyncio.to_thread(_generate_preview_bytes, file_content)
        preview_key = f"photos/previews/{fid}.jpg"
        await s3_service.upload_file(
            file_data=preview_bytes,
            s3_key=preview_key,
            content_type="image/jpeg",
        )
        preview_s3_key = preview_key
    except Exception as e:
        # Non-fatal: original uploaded; preview can be generated on demand via fallback
        pass

    # 7) Save metadata to database
    await photo_repo.create_photo_meta(
        session,
        id=fid,
        s3_key=s3_key,
        original_name=original_name,
        mime=content_type,
        size=file_size,
        user_id=current_user.id,
        project_id=project_id,
        preview_s3_key=preview_s3_key,
        original_width=original_width,
        original_height=original_height,
    )

    await session.commit()
    return {"item": fid}


@router.get("/projects/{project_id}/photos", summary="List photos in project")
async def list_photos(
    project_id: str,
    limit: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(get_db),
    project_role: Tuple[Project, str] = Depends(require_project_role("owner", "editor", "viewer")),
) -> dict[str, list[PhotoOut]]:
    """List all photos in a specific project"""
    rows = await photo_repo.list_photos(
        session,
        project_id=project_id,
        limit=limit,
        offset=offset
    )
    items = []
    for r in rows:
        out = PhotoOut.model_validate(r)
        if r.preview_s3_key:
            try:
                out.preview_url = await s3_service.generate_presigned_url(r.preview_s3_key, expiration=3600)
            except Exception:
                pass
        items.append(out)
    return {"items": items}


@router.get("/projects/{project_id}/photos/{photo_id}", summary="View/download photo")
async def get_photo(
    project_id: str,
    photo_id: str,
    session: AsyncSession = Depends(get_db),
    project_role: Tuple[Project, str] = Depends(require_project_role("owner", "editor", "viewer")),
):
    """Get a specific photo from a project"""
    photo = await photo_repo.get_photo_in_project(session, photo_id, project_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    try:
        url = await s3_service.generate_presigned_url(photo.s3_key, expiration=3600)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate presigned URL: {str(e)}"
        )

    preview_url: str | None = None
    if photo.preview_s3_key:
        try:
            preview_url = await s3_service.generate_presigned_url(photo.preview_s3_key, expiration=3600)
        except Exception:
            pass

    return {"url": url, "preview_url": preview_url}


@router.get("/projects/{project_id}/photos/{photo_id}/preview", summary="Get compressed photo preview")
async def get_photo_preview(
    project_id: str,
    photo_id: str,
    session: AsyncSession = Depends(get_db),
    project_role: Tuple[Project, str] = Depends(require_project_role("owner", "editor", "viewer")),
):
    """Return photo preview: serve pre-generated S3 object if available, else generate on the fly."""
    photo = await photo_repo.get_photo_in_project(session, photo_id, project_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    # Fast path: pre-generated preview exists in S3
    if photo.preview_s3_key:
        try:
            file_bytes = await s3_service.download_file(photo.preview_s3_key)
            return Response(content=file_bytes, media_type="image/jpeg")
        except Exception:
            pass  # fall through to on-demand generation

    # Fallback: generate preview on demand (old photos without preview_s3_key)
    try:
        file_bytes = await s3_service.download_file(photo.s3_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download photo: {str(e)}")

    try:
        preview_bytes = await asyncio.to_thread(_generate_preview_bytes, file_bytes)
        return Response(content=preview_bytes, media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate preview: {str(e)}")


@router.delete("/projects/{project_id}/photos/{photo_id}", summary="Delete photo")
async def delete_photo(
    project_id: str,
    photo_id: str,
    session: AsyncSession = Depends(get_db),
    project_role: Tuple[Project, str] = Depends(require_project_role("owner", "editor")),
):
    """Delete a photo from DB and S3"""
    photo = await photo_repo.get_photo_in_project(session, photo_id, project_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    await deletion_service.delete_photo(session, photo)
    return {"ok": True, "id": photo_id}
