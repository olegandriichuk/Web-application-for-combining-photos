import json
from datetime import datetime
from typing import Optional, Tuple

from fastapi import APIRouter, HTTPException, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..services import stitch_job_service
from ..dependencies.auth import get_current_user, verify_jwt_flexible
from ..dependencies.roles import require_project_role, require_project_role_flexible
from ..models.user import User
from ..models.project import Project
from ..schemas.stitch_job import (
    StitchJobCreate,
    StitchJobOut,
    StitchJobListResponse,
    TileMetadataOut,
    JobStatus,
)

router = APIRouter()


@router.post(
    "/projects/{project_id}/stitch-jobs",
    response_model=StitchJobOut,
    status_code=201,
    summary="Create and enqueue a stitch job"
)
async def create_stitch_job(
    project_id: str,
    data: StitchJobCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    project_role: Tuple[Project, str] = Depends(require_project_role("owner", "editor")),
):
    """
    Create a new stitching job and enqueue it for processing.

    The job is added to the database with status 'queued' and
    a message is sent to Redis Streams for worker consumption.
    """
    try:
        job = await stitch_job_service.create_and_enqueue_job(
            session,
            project_id=project_id,
            user_id=current_user.id,
            data=data,
        )
        return job
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/projects/{project_id}/stitch-jobs",
    response_model=StitchJobListResponse,
    summary="List stitch jobs for a project"
)
async def list_stitch_jobs(
    project_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[JobStatus] = Query(None, description="Filter by status"),
    from_date: Optional[datetime] = Query(None, alias="from", description="Filter by start date (from)"),
    to_date: Optional[datetime] = Query(None, alias="to", description="Filter by start date (to)"),
    sort: str = Query("startDateDesc", description="Sort order: startDateDesc or startDateAsc"),
    session: AsyncSession = Depends(get_db),
    project_role: Tuple[Project, str] = Depends(require_project_role("owner", "editor", "viewer")),
):
    """
    List stitching jobs for a project with filtering and pagination.

    Query parameters:
    - page, limit: Pagination
    - status: Filter by job status (queued, running, finished, failed, canceled)
    - from, to: Filter by job creation date range
    - sort: Sort order (startDateDesc or startDateAsc)
    """
    status_value = status.value if status else None

    return await stitch_job_service.list_jobs(
        session,
        project_id=project_id,
        status=status_value,
        from_date=from_date,
        to_date=to_date,
        sort=sort,
        page=page,
        limit=limit,
    )


@router.post(
    "/projects/{project_id}/stitch-jobs/{job_id}/run",
    response_model=StitchJobOut,
    summary="Run or re-run a stitch job",
)
async def run_stitch_job(
    project_id: str,
    job_id: str,
    session: AsyncSession = Depends(get_db),
    project_role: Tuple[Project, str] = Depends(require_project_role("owner", "editor")),
):
    """
    Queue an existing stitch job for (re-)processing.

    Allowed from statuses FAILED or FINISHED.
    Rejects RUNNING (409) and QUEUED (409).
    Resets result fields, sets status to 'queued', and enqueues to Redis Streams.
    """
    try:
        return await stitch_job_service.run_stitch_job(
            session,
            job_id=job_id,
            project_id=project_id,
        )
    except LookupError:
        raise HTTPException(status_code=404, detail="Stitch job not found")
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get(
    "/projects/{project_id}/stitch-jobs/{job_id}/result",
    summary="Get presigned download URL for a finished job",
)
async def get_stitch_job_result(
    project_id: str,
    job_id: str,
    session: AsyncSession = Depends(get_db),
    project_role: Tuple[Project, str] = Depends(require_project_role("owner", "editor", "viewer")),
):
    """Returns a short-lived S3 presigned download_url for the full-resolution result file."""
    from ..services.s3_service import s3_service

    job = await stitch_job_service.get_job(
        session,
        job_id=job_id,
        project_id=project_id,
    )
    if not job:
        raise HTTPException(status_code=404, detail="Stitch job not found")
    if job.status != "finished" or not job.result_s3_key:
        raise HTTPException(status_code=404, detail="Result not available yet")

    download_url = await s3_service.generate_presigned_url(job.result_s3_key, expiration=3600)
    return {"download_url": download_url}


@router.get(
    "/projects/{project_id}/stitch-jobs/{job_id}/log",
    summary="Stream log file content for a job",
)
async def get_stitch_job_log(
    project_id: str,
    job_id: str,
    session: AsyncSession = Depends(get_db),
    project_role: Tuple[Project, str] = Depends(require_project_role("owner", "editor", "viewer")),
):
    """Streams the log file content from S3 directly — no CORS issues."""
    from ..services.s3_service import s3_service

    job = await stitch_job_service.get_job(session, job_id=job_id, project_id=project_id)
    if not job:
        raise HTTPException(status_code=404, detail="Stitch job not found")
    if not job.log_s3_key:
        raise HTTPException(status_code=404, detail="No log available for this job")
    log_content = await s3_service.download_file(job.log_s3_key)
    return Response(
        content=log_content,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{job_id}.txt"'},
    )


@router.get(
    "/projects/{project_id}/stitch-jobs/{job_id}",
    response_model=StitchJobOut,
    summary="Get a specific stitch job"
)
async def get_stitch_job(
    project_id: str,
    job_id: str,
    session: AsyncSession = Depends(get_db),
    project_role: Tuple[Project, str] = Depends(require_project_role("owner", "editor", "viewer")),
):
    """Get details of a specific stitch job."""
    job = await stitch_job_service.get_job(
        session,
        job_id=job_id,
        project_id=project_id,
    )
    if not job:
        raise HTTPException(status_code=404, detail="Stitch job not found")

    return job


@router.get(
    "/projects/{project_id}/stitch-jobs/{job_id}/tiles/metadata",
    response_model=TileMetadataOut,
    summary="Get tile viewer metadata for a finished job",
)
async def get_tile_metadata(
    project_id: str,
    job_id: str,
    session: AsyncSession = Depends(get_db),
    project_role: Tuple[Project, str] = Depends(require_project_role("owner", "editor", "viewer")),
):
    """Returns tile pyramid metadata for use with the Leaflet viewer."""
    job = await stitch_job_service.get_job(
        session,
        job_id=job_id,
        project_id=project_id,
    )
    if not job:
        raise HTTPException(status_code=404, detail="Stitch job not found")
    if not job.tiles_ready or not job.tiles_metadata:
        raise HTTPException(status_code=404, detail="Tiles not available yet")

    meta = json.loads(job.tiles_metadata)
    return TileMetadataOut(**meta)


@router.get(
    "/projects/{project_id}/stitch-jobs/{job_id}/tiles/{z}/{x}/{y}",
    summary="Get a single tile image",
)
async def get_tile(
    project_id: str,
    job_id: str,
    z: int,
    x: int,
    y: int,
    _email: str = Depends(verify_jwt_flexible),
):
    """Redirect to a presigned S3 URL for the tile.
    No DB query — tile key is deterministic from project_id + job_id in the URL.
    JWT verified via signature only (no DB lookup). Zero DB involvement per tile.
    """
    from ..services.s3_service import s3_service
    from fastapi.responses import RedirectResponse

    tile_key = f"stitch-tiles/{project_id}/{job_id}/{z}/{x}/{y}.jpg"
    try:
        presigned_url = await s3_service.generate_presigned_url(tile_key, expiration=300)
        return RedirectResponse(url=presigned_url, status_code=307)
    except Exception:
        raise HTTPException(status_code=404, detail="Tile not found")
