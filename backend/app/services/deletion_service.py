# Author: Oleg Andriichuk, xandri07
# Bachelor's thesis - Web Application for Image Stitching, FIT VUT Brno, 2026

"""Service for handling cascading deletes with S3 cleanup.

Strategy:
1. Collect all S3 keys BEFORE deletion
2. Delete from database (with commit)
3. Delete from S3 AFTER commit succeeds

This ensures:
- No orphaned DB records (worst case scenario avoided)
- S3 orphans are acceptable (can be cleaned up with periodic job)
"""

import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import User
from ..models.project import Project
from ..models.photo import Photo
from ..models.stitch_job import StitchJob
from .s3_service import s3_service

logger = logging.getLogger(__name__)


class DeletionService:
    """Handles cascading deletes with S3 cleanup."""

    async def delete_photo(
        self,
        session: AsyncSession,
        photo: Photo,
        *,
        commit: bool = True,
    ) -> str:
        """
        Delete a single photo from DB and S3.

        Args:
            session: Database session
            photo: Photo object to delete
            commit: Whether to commit the transaction

        Returns:
            The S3 key that was deleted
        """
        s3_key = photo.s3_key
        preview_s3_key = photo.preview_s3_key

        await session.delete(photo)

        if commit:
            await session.commit()

            keys_to_delete = [k for k in (s3_key, preview_s3_key) if k]
            for key in keys_to_delete:
                try:
                    await s3_service.delete_file(key)
                    logger.info(f"Deleted S3 object: {key}")
                except Exception as e:
                    logger.warning(f"Failed to delete S3 object {key}: {e}")

        return s3_key

    async def delete_project(
        self,
        session: AsyncSession,
        project: Project,
        *,
        commit: bool = True,
    ) -> list[str]:
        """
        Delete a project and all its photos/stitch job outputs from DB and S3.

        Args:
            session: Database session
            project: Project object to delete
            commit: Whether to commit the transaction

        Returns:
            List of S3 keys that were (attempted to be) deleted
        """
        photo_stmt = select(Photo.s3_key, Photo.preview_s3_key).where(Photo.project_id == project.id)
        photo_result = await session.execute(photo_stmt)
        s3_keys = []
        for orig_key, preview_key in photo_result.all():
            s3_keys.append(orig_key)
            if preview_key:
                s3_keys.append(preview_key)

        job_stmt = select(
            StitchJob.result_s3_key,
            StitchJob.log_s3_key,
            StitchJob.tiles_s3_prefix,
        ).where(StitchJob.project_id == project.id)
        job_result = await session.execute(job_stmt)
        tile_prefixes = []
        for result_key, log_key, tiles_prefix in job_result.all():
            for key in (result_key, log_key):
                if key:
                    s3_keys.append(key)
            if tiles_prefix:
                tile_prefixes.append(tiles_prefix)

        await session.delete(project)

        if commit:
            await session.commit()

            for prefix in tile_prefixes:
                tile_keys = await s3_service.list_keys_by_prefix(prefix + "/")
                s3_keys.extend(tile_keys)

            if s3_keys:
                result = await s3_service.delete_files(s3_keys)
                logger.info(
                    f"Project {project.id}: deleted {len(result['deleted'])} S3 objects, "
                    f"{len(result['errors'])} errors"
                )

        return s3_keys

    async def delete_user(
        self,
        session: AsyncSession,
        user: User,
        *,
        commit: bool = True,
    ) -> list[str]:
        """
        Delete a user and all their projects, photos, and stitch job outputs from DB and S3.

        Args:
            session: Database session
            user: User object to delete
            commit: Whether to commit the transaction

        Returns:
            List of S3 keys that were (attempted to be) deleted
        """
        photo_stmt = select(Photo.s3_key, Photo.preview_s3_key).where(Photo.user_id == user.id)
        photo_result = await session.execute(photo_stmt)
        s3_keys = []
        for orig_key, preview_key in photo_result.all():
            s3_keys.append(orig_key)
            if preview_key:
                s3_keys.append(preview_key)

        job_stmt = (
            select(
                StitchJob.result_s3_key,
                StitchJob.log_s3_key,
                StitchJob.tiles_s3_prefix,
            )
            .join(Project, StitchJob.project_id == Project.id)
            .where(Project.user_id == user.id)
        )
        job_result = await session.execute(job_stmt)
        tile_prefixes = []
        for result_key, log_key, tiles_prefix in job_result.all():
            for key in (result_key, log_key):
                if key:
                    s3_keys.append(key)
            if tiles_prefix:
                tile_prefixes.append(tiles_prefix)

        await session.delete(user)

        if commit:
            await session.commit()

            for prefix in tile_prefixes:
                tile_keys = await s3_service.list_keys_by_prefix(prefix + "/")
                s3_keys.extend(tile_keys)

            if s3_keys:
                result = await s3_service.delete_files(s3_keys)
                logger.info(
                    f"User {user.id}: deleted {len(result['deleted'])} S3 objects, "
                    f"{len(result['errors'])} errors"
                )

        return s3_keys


deletion_service = DeletionService()
