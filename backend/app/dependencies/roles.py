# Author: Oleg Andriichuk, xandri07
# Bachelor's thesis - Web Application for Image Stitching, FIT VUT Brno, 2026

from typing import Tuple
from fastapi import Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies.auth import get_current_user, get_current_user_flexible
from ..models.user import User
from ..models.project import Project
from ..repositories import projects_repository


def require_project_role(*allowed_roles: str):
    """Return a FastAPI dependency that checks membership and role."""
    async def dependency(
        project_id: str = Path(...),
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> Tuple[Project, str]:
        result = await projects_repository.get_project_with_membership_check(
            session, project_id, current_user.id
        )
        if result is None:
            raise HTTPException(status_code=404, detail="Project not found")
        project, role = result
        if role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return project, role
    return dependency


def require_project_role_flexible(*allowed_roles: str):
    """Same as require_project_role but uses get_current_user_flexible (for tile serving)."""
    async def dependency(
        project_id: str = Path(...),
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user_flexible),
    ) -> Tuple[Project, str]:
        result = await projects_repository.get_project_with_membership_check(
            session, project_id, current_user.id
        )
        if result is None:
            raise HTTPException(status_code=404, detail="Project not found")
        project, role = result
        if role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return project, role
    return dependency
