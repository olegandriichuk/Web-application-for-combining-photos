from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from typing import Optional
import json
import math

from ..repositories import stitch_jobs_repository
from ..repositories import photos_repository
from ..models.stitch_job import StitchJob
from ..schemas.stitch_job import StitchJobCreate, StitchJobOut, StitchJobListResponse
from .redis_service import redis_service


def stitch_job_to_dict(job: StitchJob) -> dict:
    """Convert StitchJob model to dict matching StitchJobOut schema."""
    return {
        "id": job.id,
        "project_id": job.project_id,
        "status": job.status,
        "exp_name": job.exp_name,
        "ref_name": job.ref_name,
        "preset_name": job.preset_name,
        "final_res": [job.final_res_height, job.final_res_width],
        "save_format": job.save_format,
        "corner_points": json.loads(job.corner_points),
        "relative_scale": job.relative_scale,
        "photo_ids": json.loads(job.photo_ids),
        "attempt": job.attempt,
        "created_at": job.created_at,
        "queued_at": job.queued_at,
        "started_at": job.started_at,
        "finished_at": job.finished_at,
        "result_s3_key": job.result_s3_key,
        "preview_s3_key": job.preview_s3_key,
        "error_message": job.error_message,
    }


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
    # Validate photo IDs belong to project
    for photo_id in data.photo_ids:
        photo = await photos_repository.get_photo_with_ownership_check(
            session,
            photo_id=photo_id,
            user_id=user_id,
            project_id=project_id,
        )
        if photo is None:
            raise ValueError(f"Photo {photo_id} not found or does not belong to this project")

    now = datetime.now(timezone.utc)

    # Create job in DB
    job = await stitch_jobs_repository.create_stitch_job(
        session,
        project_id=project_id,
        user_id=user_id,
        photo_ids=data.photo_ids,
        exp_name=data.exp_name,
        ref_name=data.ref_name,
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

    return StitchJobOut(**stitch_job_to_dict(job))


async def list_jobs(
    session: AsyncSession,
    *,
    project_id: str,
    user_id: str,
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
        user_id=user_id,
        status=status,
        from_date=from_date,
        to_date=to_date,
        sort=sort,
        limit=limit,
        offset=offset,
    )

    pages = math.ceil(total / limit) if total > 0 else 1

    return StitchJobListResponse(
        items=[StitchJobOut(**stitch_job_to_dict(job)) for job in jobs],
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
    user_id: str,
) -> Optional[StitchJobOut]:
    """Get a single stitch job by ID."""
    job = await stitch_jobs_repository.get_stitch_job_with_ownership_check(
        session,
        job_id=job_id,
        user_id=user_id,
        project_id=project_id,
    )
    if job is None:
        return None
    return StitchJobOut(**stitch_job_to_dict(job))


async def cancel_stitch_job(
    session: AsyncSession,
    *,
    job_id: str,
    project_id: str,
    user_id: str,
) -> StitchJobOut:
    """
    Cancel a stitch job.

    Only QUEUED and RUNNING jobs can be canceled.
    - FINISHED / FAILED / CANCELED → reject (409)

    For RUNNING jobs the worker will notice the canceled status
    on its next DB check and stop processing.
    """
    job = await stitch_jobs_repository.get_stitch_job_with_ownership_check(
        session, job_id=job_id, user_id=user_id, project_id=project_id
    )
    if job is None:
        raise LookupError("Stitch job not found")

    status = job.status
    if status == "canceled":
        raise ValueError("Job is already canceled")
    if status == "finished":
        raise ValueError("Cannot cancel a finished job")
    if status == "failed":
        raise ValueError("Cannot cancel a failed job")

    # QUEUED or RUNNING → cancel
    now = datetime.now(timezone.utc)
    await stitch_jobs_repository.update_stitch_job_status(
        session, job, "canceled", finished_at=now
    )
    await session.commit()

    return StitchJobOut(**stitch_job_to_dict(job))


async def run_stitch_job(
    session: AsyncSession,
    *,
    job_id: str,
    project_id: str,
    user_id: str,
) -> StitchJobOut:
    """
    Re-run an existing stitch job.

    Validates status transitions:
    - CANCELED → reject (409)
    - RUNNING  → reject (409)
    - QUEUED   → reject (409)
    - FAILED / FINISHED → allow (reset and re-enqueue)

    Returns the updated job DTO.
    Raises ValueError with a message suitable for HTTP 409 on invalid transitions.
    """
    job = await stitch_jobs_repository.get_stitch_job_with_ownership_check(
        session, job_id=job_id, user_id=user_id, project_id=project_id
    )
    if job is None:
        raise LookupError("Stitch job not found")

    status = job.status
    if status == "canceled":
        raise ValueError("Cannot run a canceled job")
    if status == "running":
        raise ValueError("Job is already running")
    if status == "queued":
        raise ValueError("Job is already queued")

    # FAILED or FINISHED → reset and re-queue
    now = datetime.now(timezone.utc)
    await stitch_jobs_repository.reset_job_for_requeue(session, job, queued_at=now)
    await session.commit()

    await redis_service.enqueue_stitch_job(job.id)

    return StitchJobOut(**stitch_job_to_dict(job))
