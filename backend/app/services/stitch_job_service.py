# Author: Oleg Andriichuk, xandri07
# Bachelor's thesis - Web Application for Image Stitching, FIT VUT Brno, 2026

from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from typing import Optional
import math

from ..repositories import stitch_jobs_repository
from ..repositories import photos_repository
from ..models.stitch_job import StitchJob
from ..schemas.stitch_job import StitchJobCreate, StitchJobOut, StitchJobListResponse
from .redis_service import redis_service



async def create_and_enqueue_job(
    session: AsyncSession,
    *,
    project_id: str,
    user_id: str,
    data: StitchJobCreate,
) -> StitchJobOut:
    """
    Create a stitch job, save to DB, and enqueue to Redis.

    Validates that all photo IDs belong to the project.
    """
    # Validate photo IDs belong to project and find reference photo ID
    ref_photo_id = None
    for photo_id in data.photo_ids:
        photo = await photos_repository.get_photo_in_project(
            session,
            photo_id=photo_id,
            project_id=project_id,
        )
        if photo is None:
            raise ValueError(f"Photo {photo_id} not found or does not belong to this project")
        if photo.original_name == data.ref_name:
            ref_photo_id = photo.id

    now = datetime.now(timezone.utc)

    # Create job in DB
    job = await stitch_jobs_repository.create_stitch_job(
        session,
        project_id=project_id,
        user_id=user_id,
        photo_ids=data.photo_ids,
        exp_name=data.exp_name,
        ref_name=data.ref_name,
        ref_photo_id=ref_photo_id,
        preset_name=data.preset_name.value,
        final_res=data.final_res,
        save_format=data.save_format.value,
        corner_points=data.corner_points,
        relative_scale=data.relative_scale,
    )
    job.queued_at = now

    # Commit first to ensure DB record exists before enqueue
    await session.commit()

    # Enqueue to Redis (optional - if Redis is enabled)
    await redis_service.enqueue_stitch_job(job.id)

    return StitchJobOut.model_validate(job)


async def list_jobs(
    session: AsyncSession,
    *,
    project_id: str,
    status: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    sort: str = "startDateDesc",
    page: int = 1,
    limit: int = 20,
) -> StitchJobListResponse:
    """List stitch jobs with pagination and filtering."""
    offset = (page - 1) * limit

    jobs, total = await stitch_jobs_repository.list_stitch_jobs(
        session,
        project_id=project_id,
        status=status,
        from_date=from_date,
        to_date=to_date,
        sort=sort,
        limit=limit,
        offset=offset,
    )

    pages = math.ceil(total / limit) if total > 0 else 1

    return StitchJobListResponse(
        items=[StitchJobOut.model_validate(job) for job in jobs],
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )


async def get_job(
    session: AsyncSession,
    *,
    job_id: str,
    project_id: str,
) -> Optional[StitchJobOut]:
    """Get a single stitch job by ID."""
    job = await stitch_jobs_repository.get_stitch_job_in_project(
        session,
        job_id=job_id,
        project_id=project_id,
    )
    if job is None:
        return None
    return StitchJobOut.model_validate(job)


async def run_stitch_job(
    session: AsyncSession,
    *,
    job_id: str,
    project_id: str,
) -> StitchJobOut:
    """
    Re-run an existing stitch job.

    Validates status transitions:
    - RUNNING  → reject (409)
    - QUEUED   → reject (409)
    - FAILED / FINISHED → allow (reset and re-enqueue)

    Returns the updated job DTO.
    Raises ValueError with a message suitable for HTTP 409 on invalid transitions.
    """
    job = await stitch_jobs_repository.get_stitch_job_in_project(
        session, job_id=job_id, project_id=project_id
    )
    if job is None:
        raise LookupError("Stitch job not found")

    status = job.status
    if status == "running":
        raise ValueError("Job is already running")
    if status == "queued":
        raise ValueError("Job is already queued")

    # FAILED or FINISHED → reset and re-queue
    now = datetime.now(timezone.utc)
    await stitch_jobs_repository.reset_job_for_requeue(session, job, queued_at=now)
    await session.commit()

    await redis_service.enqueue_stitch_job(job.id)

    return StitchJobOut.model_validate(job)
