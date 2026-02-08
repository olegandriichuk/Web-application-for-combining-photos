import os
import uuid
from io import BytesIO

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..repositories import photos_repository as photo_repo
from ..repositories import projects_repository as project_repo
from ..services.s3_service import s3_service
from ..services.deletion_service import deletion_service
from ..dependencies.auth import get_current_user
from ..models.user import User
from ..schemas.photo import PhotoOut

router = APIRouter()


def _safe_ext(name: str | None) -> str:
    if not name:
        return ""
    _, ext = os.path.splitext(name)
    return ext if 0 < len(ext) <= 10 else ""


@router.post("/projects/{project_id}/photos", summary="Upload single photo to project g")
async def upload_photo(
    project_id: str,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload ONE photo to a specific project.
    Returns: {"item": "<photo_id>"}
    """
    # 1) Verify project exists and user is owner
    project = await project_repo.get_project_with_ownership_check(
        session, project_id, current_user.id
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

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

    # 4) Upload to S3
    try:
        await s3_service.upload_file(
            file_data=file_content,
            s3_key=s3_key,
            content_type=content_type,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file to S3: {str(e)}")

    # 5) Save metadata to database
    await photo_repo.create_photo_meta(
        session,
        id=fid,
        s3_key=s3_key,
        original_name=original_name,
        mime=content_type,
        size=file_size,
        user_id=current_user.id,
        project_id=project_id,
    )

    await session.commit()
    return {"item": fid}


@router.get("/projects/{project_id}/photos", summary="List photos in project")
async def list_photos(
    project_id: str,
    limit: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, list[PhotoOut]]:
    """List all photos in a specific project"""
    # Verify project ownership
    project = await project_repo.get_project_with_ownership_check(
        session, project_id, current_user.id
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    rows = await photo_repo.list_photos(
        session,
        user_id=current_user.id,
        project_id=project_id,
        limit=limit,
        offset=offset
    )
    return {"items": [PhotoOut.model_validate(r) for r in rows]}


@router.get("/projects/{project_id}/photos/{photo_id}", summary="View/download photo")
async def get_photo(
    project_id: str,
    photo_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific photo from a project"""
    # Verify project ownership
    project = await project_repo.get_project_with_ownership_check(
        session, project_id, current_user.id
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get photo with triple check: exists, belongs to user, belongs to project
    photo = await photo_repo.get_photo_with_ownership_check(
        session, photo_id, current_user.id, project_id
    )
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    # Download from S3
    try:
        file_data = await s3_service.download_file(photo.s3_key)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to download file from S3: {str(e)}"
        )

    # Return as streaming response
    return StreamingResponse(
        BytesIO(file_data),
        media_type=photo.mime,
        headers={"Content-Disposition": f'inline; filename="{photo.original_name}"'},
    )


@router.delete("/projects/{project_id}/photos/{photo_id}", summary="Delete photo")
async def delete_photo(
    project_id: str,
    photo_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a photo from DB and S3"""
    project = await project_repo.get_project_with_ownership_check(
        session, project_id, current_user.id
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    photo = await photo_repo.get_photo_with_ownership_check(
        session, photo_id, current_user.id, project_id
    )
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    await deletion_service.delete_photo(session, photo)
    return {"ok": True, "id": photo_id}
