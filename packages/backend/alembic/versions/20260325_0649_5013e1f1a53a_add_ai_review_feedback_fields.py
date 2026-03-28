"""add_ai_review_feedback_fields

Revision ID: 5013e1f1a53a
Revises: a1b2c3d4e5f6
Create Date: 2026-03-25 06:49:56.611410+00:00

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "5013e1f1a53a"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add AI review feedback fields to outputs table
    op.add_column(
        "outputs",
        sa.Column(
            "ai_review_flagged_categories",
            postgresql.ARRAY(sa.String(50)),
            nullable=True,
        ),
    )
    op.add_column(
        "outputs",
        sa.Column("ai_review_feedback", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    # Remove AI review feedback fields
    op.drop_column("outputs", "ai_review_feedback")
    op.drop_column("outputs", "ai_review_flagged_categories")
