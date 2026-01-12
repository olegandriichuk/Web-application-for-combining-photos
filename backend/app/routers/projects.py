from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies.auth import get_current_user
from ..models.user import User
from ..schemas.project import ProjectCreate, ProjectOut, ProjectWithPhotoCount
from ..repositories import projects_repository as repo
from ..services.deletion_service import deletion_service

router = APIRouter()


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new project"""
    project = await repo.create_project(
        session,
        user_id=current_user.id,
        name=project_data.name,
        description=project_data.description,
    )
    await session.commit()
    await session.refresh(project)
    return project


@router.get("", response_model=List[ProjectWithPhotoCount])
async def list_projects(
    limit: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all projects for the current user"""
    projects = await repo.list_projects_with_photo_count(
        session,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )
    return projects


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(
    project_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific project"""
    project = await repo.get_project_with_ownership_check(
        session, project_id, current_user.id
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    return project


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a project and all its photos (DB + S3)"""
    project = await repo.get_project_with_ownership_check(
        session, project_id, current_user.id
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    await deletion_service.delete_project(session, project)
    return {"ok": True, "id": project_id}
