from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
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
        "created_at": job.created_at,
        "started_at": job.started_at,
        "finished_at": job.finished_at,
        "result_s3_key": job.result_s3_key,
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

    # Commit first to ensure DB record exists before enqueue
    await session.commit()

    # Enqueue to Redis (optional - if Redis is enabled)
    await redis_service.enqueue_stitch_job(job.id, project_id)

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
