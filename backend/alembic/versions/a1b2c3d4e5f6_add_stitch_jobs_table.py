"""add_stitch_jobs_table

Revision ID: a1b2c3d4e5f6
Revises: 2805fba6608e
Create Date: 2026-02-09 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '2805fba6608e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('stitch_jobs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='queued'),
        sa.Column('attempt', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('exp_name', sa.String(length=255), nullable=False),
        sa.Column('ref_name', sa.String(length=255), nullable=False),
        sa.Column('preset_name', sa.String(length=50), nullable=False),
        sa.Column('final_res_height', sa.Integer(), nullable=False),
        sa.Column('final_res_width', sa.Integer(), nullable=False),
        sa.Column('save_format', sa.String(length=10), nullable=False),
        sa.Column('corner_points', sa.Text(), nullable=False),
        sa.Column('relative_scale', sa.Float(), nullable=False),
        sa.Column('photo_ids', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('queued_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('result_s3_key', sa.String(length=500), nullable=True),
        sa.Column('log_s3_key', sa.String(length=500), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_stitch_jobs_project_id'), 'stitch_jobs', ['project_id'], unique=False)
    op.create_index(op.f('ix_stitch_jobs_status'), 'stitch_jobs', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_stitch_jobs_status'), table_name='stitch_jobs')
    op.drop_index(op.f('ix_stitch_jobs_project_id'), table_name='stitch_jobs')
    op.drop_table('stitch_jobs')
