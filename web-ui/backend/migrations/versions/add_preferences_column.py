"""add preferences column

Revision ID: add_preferences_column
Revises:
Create Date: 2024-03-20

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite


# revision identifiers, used by Alembic.
revision = "add_preferences_column"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Skip adding preferences column since it's handled in database.py
    # Instead, just initialize any NULL preferences
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            UPDATE users 
            SET preferences = '{"theme": "light", "language": "en", "notifications": true, "dashboard_layout": {}}'
            WHERE preferences IS NULL
            """
        )
    )


def downgrade():
    # No downgrade needed since column is managed by SQLAlchemy models
    pass
