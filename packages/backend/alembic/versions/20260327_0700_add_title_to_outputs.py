"""add title to outputs

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f7
Create Date: 2026-03-27 07:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add title field to outputs table
    op.add_column(
        "outputs",
        sa.Column("title", sa.String(200), nullable=True),
    )


def downgrade() -> None:
    # Remove title field
    op.drop_column("outputs", "title")
