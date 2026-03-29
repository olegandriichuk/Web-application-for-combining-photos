"""add original_width_height to photos

Revision ID: 8b9415939619
Revises: d4e5f6a7b8c9
Create Date: 2026-03-28 19:20:39.606591

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8b9415939619'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('photos', sa.Column('original_width', sa.Integer(), nullable=True))
    op.add_column('photos', sa.Column('original_height', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('photos', 'original_height')
    op.drop_column('photos', 'original_width')
