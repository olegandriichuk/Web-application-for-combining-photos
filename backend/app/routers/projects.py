import json
from typing import List, Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies.auth import get_current_user
from ..dependencies.roles import require_project_role
from ..models.user import User
from ..models.project import Project
from ..schemas.project import ProjectCreate, ProjectUpdate, ProjectOut, ProjectWithPhotoCount
from ..repositories import projects_repository as repo
from ..repositories import project_members_repository as members_repo
from ..services.deletion_service import deletion_service

router = APIRouter()


def _project_out(project: Project, role: str) -> dict:
    return {
        'id': project.id,
        'user_id': project.user_id,
        'name': project.name,
        'description': project.description,
        'region': project.region,
        'year': project.year,
        'document_type': project.document_type,
        'institution': project.institution,
        'collection': project.collection,
        'is_private': project.is_private,
        'created_at': project.created_at,
        'role': role,
    }


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
        region=project_data.region,
        year=project_data.year,
        document_type=project_data.document_type,
        institution=project_data.institution,
        collection=project_data.collection,
        is_private=project_data.is_private,
    )
    await members_repo.add_member(session, project.id, current_user.id, "owner")
    await session.commit()
    await session.refresh(project)
    return _project_out(project, 'owner')


@router.get("", response_model=List[ProjectWithPhotoCount])
async def list_projects(
    limit: int = 100,
    offset: int = 0,
    search: Optional[str] = Query(None),
    conditions: Optional[str] = Query(None),
    logic: Optional[str] = Query(None),
    is_private: Optional[bool] = Query(None),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List projects visible to the current user (member + public), with optional filters.

    - ``search``: quick name contains search
    - ``conditions``: JSON array of condition objects ``{field, operator, value}``
    - ``logic``: logic expression combining condition numbers, e.g. ``(1 OR 2) AND NOT 3``
    """
    parsed_conditions: list = []
    if conditions:
        try:
            parsed_conditions = json.loads(conditions)
            if not isinstance(parsed_conditions, list):
                raise ValueError
        except Exception:
            raise HTTPException(status_code=422, detail="Invalid conditions JSON")

    projects = await repo.list_projects_with_photo_count(
        session,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        search=search,
        conditions=parsed_conditions,
        logic=logic,
        is_private=is_private,
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
    return _project_out(project, role)


@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_data: ProjectUpdate,
    session: AsyncSession = Depends(get_db),
    project_role: Tuple[Project, str] = Depends(require_project_role("owner")),
):
    """Update project metadata (owner only)"""
    project, role = project_role
    project = await repo.update_project(
        session,
        project,
        name=project_data.name,
        description=project_data.description,
        region=project_data.region,
        year=project_data.year,
        document_type=project_data.document_type,
        institution=project_data.institution,
        collection=project_data.collection,
        is_private=project_data.is_private,
    )
    await session.commit()
    await session.refresh(project)
    return _project_out(project, role)


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
