from typing import List, Tuple
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies.auth import get_current_user
from ..dependencies.roles import require_project_role
from ..models.user import User
from ..models.project import Project
from ..schemas.project import ProjectCreate, ProjectOut, ProjectWithPhotoCount
from ..repositories import projects_repository as repo
from ..repositories import project_members_repository as members_repo
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
    await members_repo.add_member(session, project.id, current_user.id, "owner")
    await session.commit()
    await session.refresh(project)
    return {
        'id': project.id,
        'user_id': project.user_id,
        'name': project.name,
        'description': project.description,
        'created_at': project.created_at,
        'role': 'owner',
    }


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
    result = await repo.get_project_with_membership_check(
        session, project_id, current_user.id
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    project, role = result
    return {
        'id': project.id,
        'user_id': project.user_id,
        'name': project.name,
        'description': project.description,
        'created_at': project.created_at,
        'role': role,
    }


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    session: AsyncSession = Depends(get_db),
    project_role: Tuple[Project, str] = Depends(require_project_role("owner")),
):
    """Delete a project and all its photos (DB + S3)"""
    project, _ = project_role
    await deletion_service.delete_project(session, project)
    return {"ok": True, "id": project_id}
