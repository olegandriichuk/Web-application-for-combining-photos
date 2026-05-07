# Author: Oleg Andriichuk, xandri07
# Bachelor's thesis - Web Application for Image Stitching, FIT VUT Brno, 2026

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
import uuid
import json

from ..models.stitch_job import StitchJob


async def create_stitch_job(
    session: AsyncSession,
    *,
    project_id: str,
    user_id: str,
    photo_ids: list[str],
    exp_name: str,
    ref_name: str,
    ref_photo_id: Optional[str],
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
        ref_photo_id=ref_photo_id,
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


async def get_stitch_job_in_project(
    session: AsyncSession,
    job_id: str,
    project_id: str,
) -> Optional[StitchJob]:
    """Get a stitch job only if it belongs to the project."""
    stmt = select(StitchJob).where(
        StitchJob.id == job_id,
        StitchJob.project_id == project_id,
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_stitch_jobs(
    session: AsyncSession,
    *,
    project_id: str,
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
    job.tiles_s3_prefix = None
    job.tiles_metadata = None
    job.tiles_ready = False
    await session.flush()
    return job


