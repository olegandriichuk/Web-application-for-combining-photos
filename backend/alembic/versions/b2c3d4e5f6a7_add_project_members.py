"""add project members

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'project_members',
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('role', sa.String(20), nullable=False),
    )
    op.create_index('ix_project_members_user_id', 'project_members', ['user_id'])

    # Seed one owner row per existing project
    op.get_bind().execute(sa.text(
        "INSERT INTO project_members (project_id, user_id, role) SELECT id, user_id, 'owner' FROM projects"
    ))


def downgrade() -> None:
    op.drop_index('ix_project_members_user_id', table_name='project_members')
    op.drop_table('project_members')
