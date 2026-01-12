"""add_projects_table_and_project_id_to_photos

Revision ID: 3e38d4d02290
Revises: 86b1e44f83e8
Create Date: 2026-01-06 19:41:38.943513

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3e38d4d02290'
down_revision: Union[str, None] = '86b1e44f83e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create projects table
    op.create_table('projects',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_projects_user_id'), 'projects', ['user_id'], unique=False)

    # Add project_id to photos using batch mode for SQLite
    with op.batch_alter_table('photos', schema=None) as batch_op:
        batch_op.add_column(sa.Column('project_id', sa.String(length=36), nullable=True))
        batch_op.create_index('ix_photos_project_id', ['project_id'], unique=False)
        batch_op.create_foreign_key('fk_photos_project_id', 'projects', ['project_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    # Remove project_id from photos using batch mode for SQLite
    with op.batch_alter_table('photos', schema=None) as batch_op:
        batch_op.drop_constraint('fk_photos_project_id', type_='foreignkey')
        batch_op.drop_index('ix_photos_project_id')
        batch_op.drop_column('project_id')

    # Drop projects table
    op.drop_index(op.f('ix_projects_user_id'), table_name='projects')
    op.drop_table('projects')
