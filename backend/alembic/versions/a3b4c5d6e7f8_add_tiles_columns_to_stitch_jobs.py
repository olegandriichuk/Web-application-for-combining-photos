"""add tiles columns to stitch_jobs

Revision ID: a3b4c5d6e7f8
Revises: fee747d7d964
Create Date: 2026-04-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a3b4c5d6e7f8'
down_revision: Union[str, None] = 'fee747d7d964'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('stitch_jobs', sa.Column('tiles_s3_prefix', sa.String(length=500), nullable=True))
    op.add_column('stitch_jobs', sa.Column('tiles_metadata', sa.Text(), nullable=True))
    op.add_column('stitch_jobs', sa.Column('tiles_ready', sa.Boolean(), server_default=sa.false(), nullable=False))


def downgrade() -> None:
    op.drop_column('stitch_jobs', 'tiles_ready')
    op.drop_column('stitch_jobs', 'tiles_metadata')
    op.drop_column('stitch_jobs', 'tiles_s3_prefix')
