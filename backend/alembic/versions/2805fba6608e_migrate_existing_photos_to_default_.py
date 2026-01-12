"""migrate_existing_photos_to_default_projects

Revision ID: 2805fba6608e
Revises: 3e38d4d02290
Create Date: 2026-01-06 19:52:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
import uuid


# revision identifiers, used by Alembic.
revision: str = '2805fba6608e'
down_revision: Union[str, None] = '3e38d4d02290'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Get connection
    conn = op.get_bind()

    # Get all users who have photos
    users_with_photos = conn.execute(text("""
        SELECT DISTINCT user_id FROM photos WHERE project_id IS NULL
    """)).fetchall()

    # For each user, create a default project and assign their photos
    for (user_id,) in users_with_photos:
        # Generate UUID for default project
        project_id = str(uuid.uuid4())

        # Insert default project
        conn.execute(text("""
            INSERT INTO projects (id, user_id, name, description, created_at)
            VALUES (:project_id, :user_id, 'Default Project',
                    'Automatically created for existing photos',
                    datetime('now'))
        """), {'project_id': project_id, 'user_id': user_id})

        # Assign all user's photos without project_id to this default project
        conn.execute(text("""
            UPDATE photos
            SET project_id = :project_id
            WHERE user_id = :user_id AND project_id IS NULL
        """), {'project_id': project_id, 'user_id': user_id})

    # Now make project_id NOT NULL using batch mode for SQLite
    with op.batch_alter_table('photos', schema=None) as batch_op:
        batch_op.alter_column('project_id',
                              existing_type=sa.String(length=36),
                              nullable=False)


def downgrade() -> None:
    # Make project_id nullable again
    with op.batch_alter_table('photos', schema=None) as batch_op:
        batch_op.alter_column('project_id',
                              existing_type=sa.String(length=36),
                              nullable=True)

    # Delete all "Default Project" projects
    conn = op.get_bind()
    conn.execute(text("""
        DELETE FROM projects WHERE name = 'Default Project'
    """))
