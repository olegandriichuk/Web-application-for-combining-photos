import re
import uuid
from typing import Any, List, Optional, Tuple

from sqlalchemy import and_, case, func, not_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.photo import Photo
from ..models.project import Project
from ..models.project_member import ProjectMember

# ── Filter condition helpers ──────────────────────────────────────────────────

_ALLOWED_FIELDS = frozenset(
    ('name', 'description', 'region', 'year', 'institution', 'collection', 'document_type')
)


def _build_condition_clause(condition: dict) -> Any:
    """Convert a single condition dict into a SQLAlchemy column expression."""
    field = condition.get('field')
    operator = condition.get('operator')
    value = condition.get('value')

    if field not in _ALLOWED_FIELDS:
        raise ValueError(f"Invalid filter field: {field!r}")

    col = getattr(Project, field)

    if operator == 'is_null':
        return col.is_(None)
    if operator == 'is_not_null':
        return col.isnot(None)
    if operator == 'contains':
        return col.ilike(f'%{value}%')
    if operator == 'not_contains':
        return ~col.ilike(f'%{value}%')
    if operator == 'equals':
        return col == value
    if operator == 'not_equal':
        return col != value
    if operator == 'gt':
        return col > value
    if operator == 'lt':
        return col < value
    raise ValueError(f"Invalid filter operator: {operator!r}")


def _tokenize(expr: str) -> List[str]:
    return re.findall(r'AND|OR|NOT|[()]|\d+', expr.upper())


def _parse_logic(tokens: List[str], clauses: List[Any]) -> Any:
    """Recursive-descent parser for boolean logic expressions.

    Supports: ``AND``, ``OR``, ``NOT``, parentheses, and condition numbers (1-based).
    Grammar::

        expr  := or_expr
        or    := and_expr ('OR' and_expr)*
        and   := not_expr ('AND' not_expr)*
        not   := 'NOT' not_expr | atom
        atom  := NUMBER | '(' expr ')'
    """
    pos = [0]

    def peek() -> Optional[str]:
        return tokens[pos[0]] if pos[0] < len(tokens) else None

    def consume() -> str:
        tok = tokens[pos[0]]
        pos[0] += 1
        return tok

    def parse_or() -> Any:
        left = parse_and()
        while peek() == 'OR':
            consume()
            left = or_(left, parse_and())
        return left

    def parse_and() -> Any:
        left = parse_not()
        while peek() == 'AND':
            consume()
            left = and_(left, parse_not())
        return left

    def parse_not() -> Any:
        if peek() == 'NOT':
            consume()
            return not_(parse_not())
        return parse_atom()

    def parse_atom() -> Any:
        tok = consume()
        if tok == '(':
            inner = parse_or()
            consume()  # ')'
            return inner
        idx = int(tok) - 1  # 1-based → 0-based
        if idx < 0 or idx >= len(clauses):
            raise ValueError(f"Condition {idx + 1} out of range")
        return clauses[idx]

    return parse_or()


async def create_project(
    session: AsyncSession,
    *,
    user_id: str,
    name: str,
    description: str | None = None,
    region: str | None = None,
    year: int | None = None,
    document_type: str | None = None,
    institution: str | None = None,
    collection: str | None = None,
    is_private: bool = False,
) -> Project:
    """Create a new project"""
    project = Project(
        id=str(uuid.uuid4()),
        user_id=user_id,
        name=name,
        description=description,
        region=region,
        year=year,
        document_type=document_type,
        institution=institution,
        collection=collection,
        is_private=is_private,
    )
    session.add(project)
    await session.flush()
    return project


async def update_project(
    session: AsyncSession,
    project: Project,
    *,
    name: str | None = None,
    description: str | None = None,
    region: str | None = None,
    year: int | None = None,
    document_type: str | None = None,
    institution: str | None = None,
    collection: str | None = None,
    is_private: bool | None = None,
) -> Project:
    """Update mutable project fields (only non-None values are applied)."""
    if name is not None:
        project.name = name
    if description is not None:
        project.description = description
    if region is not None:
        project.region = region
    if year is not None:
        project.year = year
    if document_type is not None:
        project.document_type = document_type
    if institution is not None:
        project.institution = institution
    if collection is not None:
        project.collection = collection
    if is_private is not None:
        project.is_private = is_private
    await session.flush()
    return project


async def get_project(
    session: AsyncSession,
    project_id: str
) -> Optional[Project]:
    """Get a project by ID"""
    return await session.get(Project, project_id)


async def get_project_with_membership_check(
    session: AsyncSession,
    project_id: str,
    user_id: str,
) -> Optional[Tuple[Project, str]]:
    """Get a project and the user's effective role.

    Public projects (is_private=False) are accessible to any authenticated user
    with an effective role of 'viewer'. If the user has an explicit membership,
    that role is used instead.
    """
    stmt = (
        select(Project, ProjectMember.role)
        .outerjoin(
            ProjectMember,
            (ProjectMember.project_id == Project.id) & (ProjectMember.user_id == user_id)
        )
        .where(Project.id == project_id)
        .where(
            or_(
                ProjectMember.user_id.isnot(None),  # user is a member
                Project.is_private == False,         # or project is public
            )
        )
    )
    result = await session.execute(stmt)
    row = result.one_or_none()
    if row is None:
        return None
    project, role = row[0], row[1]
    return project, role if role is not None else 'viewer'


async def list_projects_with_photo_count(
    session: AsyncSession,
    *,
    user_id: str,
    limit: int = 100,
    offset: int = 0,
    search: str | None = None,
    conditions: list | None = None,
    logic: str | None = None,
    is_private: bool | None = None,
) -> List[dict]:
    """List projects visible to the user (member projects + public projects) with photo counts and roles."""
    stmt = (
        select(
            Project,
            func.count(Photo.id).label('photo_count'),
            case(
                (ProjectMember.role.isnot(None), ProjectMember.role),
                else_='viewer'
            ).label('effective_role'),
        )
        .outerjoin(
            ProjectMember,
            (ProjectMember.project_id == Project.id) & (ProjectMember.user_id == user_id)
        )
        .outerjoin(Photo, Photo.project_id == Project.id)
        .where(
            or_(
                ProjectMember.user_id.isnot(None),
                Project.is_private == False,
            )
        )
        .group_by(Project.id, ProjectMember.role)
        .order_by(Project.created_at.desc())
    )

    # Quick name search (search bar)
    if search:
        stmt = stmt.where(Project.name.ilike(f'%{search}%'))

    # Advanced condition-based filters
    if conditions:
        clauses = [_build_condition_clause(c) for c in conditions]
        if len(clauses) == 1:
            stmt = stmt.where(clauses[0])
        elif logic:
            tokens = _tokenize(logic)
            combined = _parse_logic(tokens, clauses)
            stmt = stmt.where(combined)
        else:
            stmt = stmt.where(and_(*clauses))

    if is_private is not None:
        stmt = stmt.where(Project.is_private == is_private)

    stmt = stmt.limit(limit).offset(offset)
    result = await session.execute(stmt)

    projects = []
    for project, photo_count, role in result.all():
        projects.append({
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
            'photo_count': photo_count or 0,
            'role': role,
        })
    return projects
