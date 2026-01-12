from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ..models.project import Project
from ..models.photo import Photo
import uuid


async def create_project(
    session: AsyncSession,
    *,
    user_id: str,
    name: str,
    description: str | None = None,
) -> Project:
    """Create a new project"""
    project = Project(
        id=str(uuid.uuid4()),
        user_id=user_id,
        name=name,
        description=description,
    )
    session.add(project)
    await session.flush()
    return project


async def get_project(
    session: AsyncSession,
    project_id: str
) -> Optional[Project]:
    """Get a project by ID"""
    return await session.get(Project, project_id)


async def get_project_with_ownership_check(
    session: AsyncSession,
    project_id: str,
    user_id: str,
) -> Optional[Project]:
    """Get a project only if it belongs to the user"""
    stmt = select(Project).where(
        Project.id == project_id,
        Project.user_id == user_id
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_projects(
    session: AsyncSession,
    *,
    user_id: str,
    limit: int = 100,
    offset: int = 0,
) -> List[Project]:
    """List all projects for a user"""
    stmt = (
        select(Project)
        .where(Project.user_id == user_id)
        .order_by(Project.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def list_projects_with_photo_count(
    session: AsyncSession,
    *,
    user_id: str,
    limit: int = 100,
    offset: int = 0,
) -> List[dict]:
    """List projects with photo counts"""
    stmt = (
        select(
            Project,
            func.count(Photo.id).label('photo_count')
        )
        .outerjoin(Photo, Photo.project_id == Project.id)
        .where(Project.user_id == user_id)
        .group_by(Project.id)
        .order_by(Project.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)

    # Convert to list of dicts with project data and photo_count
    projects = []
    for project, photo_count in result.all():
        projects.append({
            'id': project.id,
            'user_id': project.user_id,
            'name': project.name,
            'description': project.description,
            'created_at': project.created_at,
            'photo_count': photo_count or 0,
        })
    return projects


async def update_project(
    session: AsyncSession,
    project: Project,
    *,
    name: str | None = None,
    description: str | None = None,
) -> Project:
    """Update a project"""
    if name is not None:
        project.name = name
    if description is not None:
        project.description = description
    await session.flush()
    return project


async def delete_project(
    session: AsyncSession,
    project: Project
) -> None:
    """Delete a project (will cascade delete photos)"""
    await session.delete(project)
