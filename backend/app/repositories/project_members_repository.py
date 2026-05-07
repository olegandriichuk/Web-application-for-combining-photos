# Author: Oleg Andriichuk, xandri07
# Bachelor's thesis - Web Application for Image Stitching, FIT VUT Brno, 2026

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from ..models.project_member import ProjectMember


async def add_member(
    session: AsyncSession,
    project_id: str,
    user_id: str,
    role: str,
) -> ProjectMember:
    member = ProjectMember(project_id=project_id, user_id=user_id, role=role)
    session.add(member)
    await session.flush()
    return member


async def get_member(
    session: AsyncSession,
    project_id: str,
    user_id: str,
) -> Optional[ProjectMember]:
    return await session.get(ProjectMember, (project_id, user_id))


async def list_members(
    session: AsyncSession,
    project_id: str,
) -> list[ProjectMember]:
    stmt = (
        select(ProjectMember)
        .where(ProjectMember.project_id == project_id)
        .options(joinedload(ProjectMember.user))
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def update_member_role(
    session: AsyncSession,
    member: ProjectMember,
    role: str,
) -> ProjectMember:
    member.role = role
    await session.flush()
    return member


async def remove_member(
    session: AsyncSession,
    member: ProjectMember,
) -> None:
    await session.delete(member)
