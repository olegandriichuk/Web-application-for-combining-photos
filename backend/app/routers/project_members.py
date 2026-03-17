from typing import List, Tuple

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies.auth import get_current_user
from ..dependencies.roles import require_project_role
from ..models.user import User
from ..models.project import Project
from ..repositories import project_members_repository as members_repo
from ..repositories import users_repository
from ..schemas.project_member import ProjectMemberOut, AddMemberRequest, UpdateMemberRoleRequest

router = APIRouter()


def _member_to_out(member) -> ProjectMemberOut:
    return ProjectMemberOut(
        user_id=member.user_id,
        user_name=member.user.name,
        user_email=member.user.email,
        role=member.role,
    )


@router.get("/{project_id}/members", response_model=List[ProjectMemberOut])
async def list_members(
    project_id: str,
    session: AsyncSession = Depends(get_db),
    project_role: Tuple[Project, str] = Depends(require_project_role("owner")),
):
    """List all members of a project (owner only)."""
    members = await members_repo.list_members(session, project_id)
    return [_member_to_out(m) for m in members]


@router.post("/{project_id}/members", response_model=ProjectMemberOut, status_code=201)
async def add_member(
    project_id: str,
    data: AddMemberRequest,
    session: AsyncSession = Depends(get_db),
    project_role: Tuple[Project, str] = Depends(require_project_role("owner")),
):
    """Add a user to a project (owner only)."""
    if data.role not in ("editor", "viewer"):
        raise HTTPException(status_code=422, detail="Role must be 'editor' or 'viewer'")

    target_user = await users_repository.get_user_by_email(session, data.email)
    if target_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    existing = await members_repo.get_member(session, project_id, target_user.id)
    if existing is not None:
        raise HTTPException(status_code=409, detail="User is already a member of this project")

    member = await members_repo.add_member(session, project_id, target_user.id, data.role)
    await session.commit()

    return ProjectMemberOut(
        user_id=member.user_id,
        user_name=target_user.name,
        user_email=target_user.email,
        role=member.role,
    )


@router.patch("/{project_id}/members/{user_id}", response_model=ProjectMemberOut)
async def update_member_role(
    project_id: str,
    user_id: str,
    data: UpdateMemberRoleRequest,
    session: AsyncSession = Depends(get_db),
    project_role: Tuple[Project, str] = Depends(require_project_role("owner")),
):
    """Update a member's role (owner only)."""
    if data.role not in ("editor", "viewer"):
        raise HTTPException(status_code=422, detail="Role must be 'editor' or 'viewer'")

    member = await members_repo.get_member(session, project_id, user_id)
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")
    if member.role == "owner":
        raise HTTPException(status_code=403, detail="Cannot change the owner's role")

    await session.refresh(member, ["user"])
    await members_repo.update_member_role(session, member, data.role)
    await session.commit()

    return ProjectMemberOut(
        user_id=member.user_id,
        user_name=member.user.name,
        user_email=member.user.email,
        role=member.role,
    )


@router.delete("/{project_id}/members/{user_id}")
async def remove_member(
    project_id: str,
    user_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    project_role: Tuple[Project, str] = Depends(require_project_role("owner")),
):
    """Remove a member from a project (owner only)."""
    if user_id == current_user.id:
        raise HTTPException(status_code=403, detail="Owner cannot remove themselves")

    member = await members_repo.get_member(session, project_id, user_id)
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")

    await members_repo.remove_member(session, member)
    await session.commit()
    return {"ok": True}
