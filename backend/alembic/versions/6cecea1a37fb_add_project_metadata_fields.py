"""add project metadata fields

Revision ID: 6cecea1a37fb
Revises: 8b9415939619
Create Date: 2026-03-28 22:23:39.373537

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6cecea1a37fb'
down_revision: Union[str, None] = '8b9415939619'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('projects', sa.Column('region', sa.String(length=200), nullable=True))
    op.add_column('projects', sa.Column('year', sa.Integer(), nullable=True))
    op.add_column('projects', sa.Column('document_type', sa.String(length=50), nullable=True))
    op.add_column('projects', sa.Column('institution', sa.String(length=200), nullable=True))
    op.add_column('projects', sa.Column('collection', sa.String(length=200), nullable=True))
    # SQLite: server_default='0' — replaced with sa.false() for unambiguous PostgreSQL boolean default
    # op.add_column('projects', sa.Column('is_private', sa.Boolean(), server_default='0', nullable=False))
    op.add_column('projects', sa.Column('is_private', sa.Boolean(), server_default=sa.false(), nullable=False))


def downgrade() -> None:
    op.drop_column('projects', 'is_private')
    op.drop_column('projects', 'collection')
    op.drop_column('projects', 'institution')
    op.drop_column('projects', 'document_type')
    op.drop_column('projects', 'year')
    op.drop_column('projects', 'region')
