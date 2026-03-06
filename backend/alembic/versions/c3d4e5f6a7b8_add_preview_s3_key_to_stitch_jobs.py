"""add_preview_s3_key_to_stitch_jobs

Revision ID: c3d4e5f6a7b8
Revises: a1b2c3d4e5f6
Create Date: 2026-02-28 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'stitch_jobs',
        sa.Column('preview_s3_key', sa.String(length=500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('stitch_jobs', 'preview_s3_key')
