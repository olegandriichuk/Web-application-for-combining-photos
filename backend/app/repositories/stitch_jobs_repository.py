from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
import uuid
import json

from ..models.stitch_job import StitchJob
from ..schemas.stitch_job import JobStatus


async def create_stitch_job(
    session: AsyncSession,
    *,
    project_id: str,
    user_id: str,
    photo_ids: list[str],
    exp_name: str,
    ref_name: str,
    preset_name: str,
    final_res: list[int],
    save_format: str,
    corner_points: list[list[int]],
    relative_scale: float,
) -> StitchJob:
    """Create a new stitch job with status 'queued'."""
    job = StitchJob(
        id=str(uuid.uuid4()),
        project_id=project_id,
        user_id=user_id,
        status="queued",
        exp_name=exp_name,
        ref_name=ref_name,
        preset_name=preset_name,
        final_res_height=final_res[0],
        final_res_width=final_res[1],
        save_format=save_format,
        corner_points=json.dumps(corner_points),
        relative_scale=relative_scale,
        photo_ids=json.dumps(photo_ids),
    )
    session.add(job)
    await session.flush()
    return job


async def get_stitch_job(
    session: AsyncSession,
    job_id: str
) -> Optional[StitchJob]:
    """Get a stitch job by ID."""
    return await session.get(StitchJob, job_id)


async def get_stitch_job_with_ownership_check(
    session: AsyncSession,
    job_id: str,
    user_id: str,
    project_id: str,
) -> Optional[StitchJob]:
    """Get a stitch job only if it belongs to the user and project."""
    stmt = select(StitchJob).where(
        StitchJob.id == job_id,
        StitchJob.user_id == user_id,
        StitchJob.project_id == project_id,
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_stitch_jobs(
    session: AsyncSession,
    *,
    project_id: str,
    user_id: str,
    status: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    sort: str = "startDateDesc",
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[StitchJob], int]:
    """
    List stitch jobs for a project with filtering and pagination.
    Returns (jobs, total_count).
    """
    # Base query
    base_stmt = select(StitchJob).where(
        StitchJob.project_id == project_id,
        StitchJob.user_id == user_id,
    )

    # Apply filters
    if status:
        base_stmt = base_stmt.where(StitchJob.status == status)
    if from_date:
        base_stmt = base_stmt.where(StitchJob.created_at >= from_date)
    if to_date:
        base_stmt = base_stmt.where(StitchJob.created_at <= to_date)

    # Count query
    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    count_result = await session.execute(count_stmt)
    total = count_result.scalar() or 0

    # Apply sorting
    if sort == "startDateAsc":
        base_stmt = base_stmt.order_by(StitchJob.created_at.asc())
    else:
        base_stmt = base_stmt.order_by(StitchJob.created_at.desc())

    # Apply pagination
    base_stmt = base_stmt.limit(limit).offset(offset)

    result = await session.execute(base_stmt)
    jobs = list(result.scalars().all())

    return jobs, total


async def update_stitch_job_status(
    session: AsyncSession,
    job: StitchJob,
    status: str,
    *,
    started_at: Optional[datetime] = None,
    finished_at: Optional[datetime] = None,
    result_s3_key: Optional[str] = None,
    log_s3_key: Optional[str] = None,
    error_message: Optional[str] = None,
) -> StitchJob:
    """Update stitch job status and related fields."""
    job.status = status
    if started_at is not None:
        job.started_at = started_at
    if finished_at is not None:
        job.finished_at = finished_at
    if result_s3_key is not None:
        job.result_s3_key = result_s3_key
    if log_s3_key is not None:
        job.log_s3_key = log_s3_key
    if error_message is not None:
        job.error_message = error_message
    await session.flush()
    return job


async def reset_job_for_requeue(
    session: AsyncSession,
    job: StitchJob,
    queued_at: datetime,
) -> StitchJob:
    """Reset a job's transient fields and set status to queued for re-run."""
    job.status = "queued"
    job.queued_at = queued_at
    job.started_at = None
    job.finished_at = None
    job.error_message = None
    job.result_s3_key = None
    job.log_s3_key = None
    job.attempt = 0
    await session.flush()
    return job


async def delete_stitch_job(
    session: AsyncSession,
    job: StitchJob
) -> None:
    """Delete a stitch job."""
    await session.delete(job)
