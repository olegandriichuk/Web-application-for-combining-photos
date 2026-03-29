"""set existing projects private

Revision ID: fee747d7d964
Revises: 6cecea1a37fb
Create Date: 2026-03-28 22:30:44.067695

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fee747d7d964'
down_revision: Union[str, None] = '6cecea1a37fb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE projects SET is_private = 1 WHERE is_private = 0")


def downgrade() -> None:
    pass
