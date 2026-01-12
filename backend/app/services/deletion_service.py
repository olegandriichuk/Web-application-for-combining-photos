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

        await session.delete(photo)

        if commit:
            await session.commit()

            try:
                await s3_service.delete_file(s3_key)
                logger.info(f"Deleted S3 object: {s3_key}")
            except Exception as e:
                logger.warning(f"Failed to delete S3 object {s3_key}: {e}")

        return s3_key

    async def delete_project(
        self,
        session: AsyncSession,
        project: Project,
        *,
        commit: bool = True,
    ) -> list[str]:
        """
        Delete a project and all its photos from DB and S3.

        Args:
            session: Database session
            project: Project object to delete
            commit: Whether to commit the transaction

        Returns:
            List of S3 keys that were (attempted to be) deleted
        """
        stmt = select(Photo.s3_key).where(Photo.project_id == project.id)
        result = await session.execute(stmt)
        s3_keys = list(result.scalars().all())

        await session.delete(project)

        if commit:
            await session.commit()

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
        Delete a user and all their projects/photos from DB and S3.

        Args:
            session: Database session
            user: User object to delete
            commit: Whether to commit the transaction

        Returns:
            List of S3 keys that were (attempted to be) deleted
        """
        stmt = select(Photo.s3_key).where(Photo.user_id == user.id)
        result = await session.execute(stmt)
        s3_keys = list(result.scalars().all())

        await session.delete(user)

        if commit:
            await session.commit()

            if s3_keys:
                result = await s3_service.delete_files(s3_keys)
                logger.info(
                    f"User {user.id}: deleted {len(result['deleted'])} S3 objects, "
                    f"{len(result['errors'])} errors"
                )

        return s3_keys


deletion_service = DeletionService()
