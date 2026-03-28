"""add originality_reasoning field

Revision ID: a1b2c3d4e5f7
Revises: 8a9b0c1d2e3f
Create Date: 2026-03-27 05:30:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f7"
down_revision = "8a9b0c1d2e3f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add originality_reasoning field to outputs table
    op.add_column(
        "outputs",
        sa.Column("originality_reasoning", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    # Remove originality_reasoning field
    op.drop_column("outputs", "originality_reasoning")
