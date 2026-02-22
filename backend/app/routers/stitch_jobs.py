from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..repositories import projects_repository as project_repo
from ..services import stitch_job_service
from ..dependencies.auth import get_current_user
from ..models.user import User
from ..schemas.stitch_job import (
    StitchJobCreate,
    StitchJobOut,
    StitchJobListResponse,
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
):
    """
    Create a new stitching job and enqueue it for processing.

    The job is added to the database with status 'queued' and
    a message is sent to Redis Streams for worker consumption.
    """
    # Verify project exists and user is owner
    project = await project_repo.get_project_with_ownership_check(
        session, project_id, current_user.id
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

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
    current_user: User = Depends(get_current_user),
):
    """
    List stitching jobs for a project with filtering and pagination.

    Query parameters:
    - page, limit: Pagination
    - status: Filter by job status (queued, running, finished, failed, canceled)
    - from, to: Filter by job creation date range
    - sort: Sort order (startDateDesc or startDateAsc)
    """
    # Verify project exists and user is owner
    project = await project_repo.get_project_with_ownership_check(
        session, project_id, current_user.id
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    status_value = status.value if status else None

    return await stitch_job_service.list_jobs(
        session,
        project_id=project_id,
        user_id=current_user.id,
        status=status_value,
        from_date=from_date,
        to_date=to_date,
        sort=sort,
        page=page,
        limit=limit,
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
    current_user: User = Depends(get_current_user),
):
    """Get details of a specific stitch job."""
    # Verify project exists and user is owner
    project = await project_repo.get_project_with_ownership_check(
        session, project_id, current_user.id
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    job = await stitch_job_service.get_job(
        session,
        job_id=job_id,
        project_id=project_id,
        user_id=current_user.id,
    )
    if not job:
        raise HTTPException(status_code=404, detail="Stitch job not found")

    return job
